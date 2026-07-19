import asyncio
import json
import logging
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Union, Optional, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agno.agent import Agent
from agno.os import AgentOS
from agno.run.agent import CustomEvent
from agents.base import build_agent
from agents.courses import find_courses
from agents.creators import discover_creators
from agents.ranking import rank_courses
from agents.reviews import validate_reviews
from agents.roadmap import build_roadmap
from cli import roadmap_to_markdown
from utils.console import save_markdown
from utils.logging import setup_logging
from utils.models import UserRequirement
from utils.settings import settings


@dataclass
class CustomReasoningStepEvent(CustomEvent):
    event: str = "ReasoningStep"
    extra_data: Optional[Dict[str, Any]] = None


# Setup logging
setup_logging()

# Create custom FastAPI app
app = FastAPI(
    title="Pathy Roadmap AI API",
    description="Backend server for generating personalized learning roadmaps",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from utils.runtime_config import set_runtime_config, get_runtime_config, clear_runtime_config, is_configured
import httpx

class ConfigPayload(BaseModel):
    api_key: str
    base_url: str
    model_name: str

@app.get("/status")
async def status_check():
    """Simple status check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/config")
async def get_config():
    """Get status of the OpenAI credentials config."""
    cfg = get_runtime_config()
    api_key = cfg.get("OPENAI_API_KEY")
    masked_key = None
    if api_key:
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "configured"
    
    from utils.runtime_config import _runtime_config
    source = "user" if _runtime_config.get("OPENAI_API_KEY") else ("env" if settings.OPENAI_API_KEY else "none")
    
    return {
        "is_configured": bool(cfg.get("OPENAI_API_KEY") and cfg.get("OPENAI_BASE_URL") and cfg.get("OPENAI_MODEL_NAME")),
        "model_name": cfg.get("OPENAI_MODEL_NAME"),
        "base_url": cfg.get("OPENAI_BASE_URL"),
        "api_key_preview": masked_key,
        "source": source
    }

@app.post("/api/config")
async def set_config(payload: ConfigPayload):
    """Validate and save OpenAI credentials overrides."""
    base_url = payload.base_url.strip()
    api_key = payload.api_key.strip()
    model_name = payload.model_name.strip()
    
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Base URL must start with http:// or https://")
        
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    test_body = {
        "model": model_name,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=test_body, headers=headers)
            if resp.status_code != 200:
                try:
                    err_json = resp.json()
                    err_detail = err_json.get("error", {}).get("message") or resp.text
                except Exception:
                    err_detail = resp.text
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed (HTTP {resp.status_code}): {err_detail}"
                )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Connection to endpoint failed: {str(exc)}"
        )
        
    set_runtime_config(api_key, base_url, model_name)
    return {"status": "success", "message": "Credentials validated and saved successfully."}

@app.delete("/api/config")
async def clear_config():
    """Clear runtime config overrides and revert to env defaults."""
    clear_runtime_config()
    return {"status": "success", "message": "Runtime config cleared, reverted to env defaults."}

@app.post("/api/generate")
async def generate_roadmap_api(requirement: UserRequirement):
    """Direct REST API endpoint to generate a roadmap from requirements."""
    if not is_configured():
        raise HTTPException(
            status_code=400,
            detail="OpenAI credentials are not configured. Please supply them in configuration settings.",
        )
    try:
        logging.info("REST API request received: %s", requirement.model_dump_json())

        # Step 1: Discover creators
        creators = await discover_creators(requirement)
        if not creators:
            raise HTTPException(
                status_code=404,
                detail="No relevant YouTube creators were found for this topic.",
            )

        # Step 2: Discover courses
        courses = await find_courses(requirement, creators)
        if not courses:
            raise HTTPException(
                status_code=404,
                detail="No eligible creator-led courses were found for this topic.",
            )

        # Step 3: Validate reviews
        reviews = await validate_reviews(courses)

        # Step 4: Rank courses
        rankings = await rank_courses(requirement, courses, reviews)
        if not rankings:
            raise HTTPException(
                status_code=404,
                detail="Could not rank any valid course candidates.",
            )

        # Step 5: Build roadmap
        selected_ranking = rankings[0]
        selected_course = next(
            course for course in courses if course.title == selected_ranking.course_title
        )

        roadmap = await build_roadmap(
            requirement=requirement,
            selected_course=selected_course,
            ranking=selected_ranking,
        )

        markdown = roadmap_to_markdown(roadmap)

        # Step 6: Save outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        markdown_path = save_markdown(f"roadmap_{timestamp}.md", markdown)

        json_path = markdown_path.with_suffix(".json")
        json_path.write_text(
            json.dumps(roadmap.model_dump(), indent=2),
            encoding="utf-8",
        )

        return {
            "status": "success",
            "markdown": markdown,
            "roadmap": roadmap.model_dump(),
            "markdown_path": str(markdown_path),
            "json_path": str(json_path),
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error("Error in generate_roadmap_api: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Agent tool definition
async def generate_learning_roadmap(
    topic: str,
    current_level: str = "beginner",
    target_outcome: str = "Build production-ready projects",
    weekly_hours: int = 8,
    preferred_language: str = "English",
) -> AsyncGenerator[Union[CustomReasoningStepEvent, str], None]:
    """Generates a personalized week-by-week learning roadmap for a topic.

    Args:
        topic: The topic or subject you want to learn (e.g., 'FastAPI', 'Machine Learning').
        current_level: Your current knowledge level (e.g., 'beginner', 'intermediate', 'advanced').
        target_outcome: What outcome you want to achieve (e.g., 'Build production-ready projects', 'Pass an exam').
        weekly_hours: Number of hours you can dedicate to learning per week.
        preferred_language: Preferred language for learning resources.

    Returns:
        The complete generated week-by-week learning roadmap in markdown format.
    """
    requirement = UserRequirement(
        topic=topic,
        current_level=current_level.lower(),
        target_outcome=target_outcome,
        weekly_hours=weekly_hours,
        preferred_language=preferred_language,
    )

    if not is_configured():
        yield "An error occurred: OpenAI credentials are not configured. Please open the Settings modal (gear icon in sidebar) to configure your API key, base URL, and model name."
        return

    try:
        logging.info("Agent tool invoked with requirements: %s", requirement.model_dump_json())

        # Step 1: Discover creators
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "🔍 Discovering YouTube creators for this topic...",
                        "reasoning": f"Querying YouTube and analyzing results to identify top-quality creators for '{topic}'...",
                        "action": "Search YouTube creators",
                        "result": "In progress",
                    }
                ]
            }
        )
        creators = await discover_creators(requirement)
        if not creators:
            yield "No relevant YouTube creators were found for this topic."
            return

        # Step 2: Discover courses
        creator_names = ", ".join([c.name for c in creators])
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "📚 Finding course candidates led by creators...",
                        "reasoning": f"Identified creators: {creator_names}. Querying YouTube playlists and channel pages for structured courses...",
                        "action": "Discover courses",
                        "result": "In progress",
                    }
                ]
            }
        )
        courses = await find_courses(requirement, creators)
        if not courses:
            yield "No eligible creator-led courses were found for this topic."
            return

        # Step 3: Validate reviews
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "💬 Gathering reviews on Reddit...",
                        "reasoning": f"Found {len(courses)} course candidates. Searching Reddit communities to gather reviews and validation evidence...",
                        "action": "Search Reddit reviews",
                        "result": "In progress",
                    }
                ]
            }
        )
        reviews = await validate_reviews(courses)

        # Step 4: Rank courses
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "🏆 Ranking courses based on criteria...",
                        "reasoning": "Finished gathering reviews. Ranking course candidates using standard weighted rubric...",
                        "action": "Rank courses",
                        "result": "In progress",
                    }
                ]
            }
        )
        rankings = await rank_courses(requirement, courses, reviews)
        if not rankings:
            yield "Could not rank any valid course candidates."
            return

        # Step 5: Build roadmap
        selected_ranking = rankings[0]
        selected_course = next(
            course for course in courses if course.title == selected_ranking.course_title
        )
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "🗺️ Building personalized week-by-week roadmap...",
                        "reasoning": f"Top ranked course: '{selected_ranking.course_title}'. Structuring week-by-week learning roadmap and querying YouTube resources...",
                        "action": "Build roadmap",
                        "result": "In progress",
                    }
                ]
            }
        )
        roadmap = await build_roadmap(
            requirement=requirement,
            selected_course=selected_course,
            ranking=selected_ranking,
        )

        markdown = roadmap_to_markdown(roadmap)

        # Step 6: Save outputs
        yield CustomReasoningStepEvent(
            created_at=int(time.time()),
            extra_data={
                "reasoning_steps": [
                    {
                        "title": "💾 Saving learning roadmap files...",
                        "reasoning": "Roadmap successfully generated. Saving markdown and JSON files to output directory...",
                        "action": "Save output",
                        "result": "In progress",
                    }
                ]
            }
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        markdown_path = save_markdown(f"roadmap_{timestamp}.md", markdown)

        json_path = markdown_path.with_suffix(".json")
        json_path.write_text(
            json.dumps(roadmap.model_dump(), indent=2),
            encoding="utf-8",
        )

        yield markdown

    except Exception as e:
        logging.error("Error in generate_learning_roadmap tool: %s", str(e), exc_info=True)
        yield f"An error occurred while generating the roadmap: {str(e)}"


from agno.db.sqlite import SqliteDb

# Build the roadmap agent to be exposed via AgentOS
roadmap_agent = build_agent(
    name="pathy-roadmap-agent",
    instructions=[
        "You are Pathy, a friendly learning assistant that helps users build custom, personalized week-by-week roadmaps.",
        "Your primary capability is generating custom roadmaps using the `generate_learning_roadmap` tool.",
        "When the user asks for a roadmap or wants to learn something, ask clarifying questions if they haven't provided details like their current level, target outcome, weekly hours, or language preference.",
        "If you have enough details, invoke the `generate_learning_roadmap` tool with the user's requirements.",
        "Once the tool returns the markdown roadmap, display the entire roadmap to the user. Do not shorten or truncate it.",
    ],
    tools=[generate_learning_roadmap],
    db=SqliteDb(db_file="sessions.db"),
)

# Pass your custom FastAPI app to AgentOS
agent_os = AgentOS(
    name="Pathy Roadmap OS",
    description="AgentOS endpoint for Pathy Roadmap AI",
    agents=[roadmap_agent],
    base_app=app,
)

# Get the combined app with both AgentOS and custom routes
app = agent_os.get_app()

if __name__ == "__main__":
    import os
    # Start AgentOS server
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "7777"))
    debug = os.getenv("DEBUG", "true").lower() in ("true", "1")
    agent_os.serve(app="server:app", host=host, port=port, reload=debug)
