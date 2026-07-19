import json
import logging
import re

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.guardrails import PromptInjectionGuardrail
from pydantic import BaseModel

from utils.settings import settings

prompt_injection_guardrail = PromptInjectionGuardrail()


from agno.db.sqlite import SqliteDb
from typing import Any

from utils.runtime_config import get_runtime_config

def sync_agent_config_pre_hook(agent: Agent) -> None:
    """Pre-hook that dynamically updates the agent's model with the latest runtime configuration right before execution."""
    cfg = get_runtime_config()
    model_name = cfg["OPENAI_MODEL_NAME"]
    api_key = cfg["OPENAI_API_KEY"]
    base_url = cfg["OPENAI_BASE_URL"]

    if agent.model and isinstance(agent.model, OpenAILike):
        agent.model.id = model_name or ""
        agent.model.api_key = api_key or ""
        agent.model.base_url = base_url or ""
        logging.info(
            "Synced agent '%s' model with runtime config: model='%s', base_url='%s'",
            agent.name,
            model_name,
            base_url
        )

def build_agent(
    name: str,
    instructions: list[str],
    output_schema: type[BaseModel] | None = None,
    tools: list | None = None,
    db: Any = None,
) -> Agent:
    cfg = get_runtime_config()
    model_name = cfg["OPENAI_MODEL_NAME"]
    api_key = cfg["OPENAI_API_KEY"]
    base_url = cfg["OPENAI_BASE_URL"]

    logging.info(
        "Building agent: '%s' with model '%s', output_schema '%s', instructions count %d, tools %s",
        name,
        model_name,
        output_schema.__name__ if output_schema and hasattr(output_schema, "__name__") else str(output_schema),
        len(instructions),
        [getattr(t, "name", str(t)) for t in tools] if tools else []
    )

    agent = Agent(
        name=name,
        model=OpenAILike(
            id=model_name or "",
            api_key=api_key or "",
            base_url=base_url or "",
        ),
        instructions=instructions,
        tools=tools or [],
        output_schema=output_schema,
        markdown=True if output_schema is None else False,
        use_json_mode=True if output_schema is not None else False,
        db=db,
        pre_hooks=[prompt_injection_guardrail, sync_agent_config_pre_hook],
    )
    return agent


def _extract_json(text: str) -> str:
    cleaned = text.strip()
    # Strip </think> reasoning blocks (some models emit these)
    if "</think>" in cleaned:
        cleaned = cleaned.split("</think>", 1)[-1].strip()
    # Strip markdown code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()
    # Slice to the outermost JSON object
    brace_start = cleaned.find("{")
    if brace_start != -1:
        cleaned = cleaned[brace_start:]
    brace_end = cleaned.rfind("}")
    if brace_end != -1:
        # Drop any trailing content after the last `}` (causes "Extra data" errors)
        cleaned = cleaned[: brace_end + 1]
    return cleaned.strip()


async def response_content(agent: Agent, prompt: str) -> BaseModel | str:
    logging.info("Running agent '%s'. Prompt length: %d chars", agent.name, len(prompt))
    try:
        response = await agent.arun(prompt)
    except Exception as e:
        logging.error("Agent '%s' execution failed: %s", agent.name, str(e), exc_info=True)
        raise e

    if response.content is None:
        msg = f"{agent.name} returned an empty response."
        logging.error(msg)
        raise RuntimeError(msg)

    content = response.content
    logging.info("Agent '%s' execution succeeded. Response length: %d chars", agent.name, len(str(content)))

    if agent.output_schema is None:
        return content

    schema_name = agent.output_schema.__name__ if hasattr(agent.output_schema, "__name__") else str(agent.output_schema)

    if isinstance(content, agent.output_schema):
        return content

    if isinstance(content, dict):
        return agent.output_schema(**content)

    if isinstance(content, str):
        raw = content
        for attempt in (_extract_json, lambda s: s.strip()):
            cleaned = attempt(raw)
            if not cleaned:
                continue
            try:
                data = json.loads(cleaned)
                return agent.output_schema(**data)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        try:
            return agent.output_schema.model_validate_json(raw)
        except Exception:
            pass

        logging.error(
            "Agent '%s' failed to parse response into %s. Raw response:\n%s",
            agent.name, schema_name, raw,
        )
        raise RuntimeError(
            f"{agent.name} failed to parse response into {schema_name}.\n"
            f"Raw response:\n{raw}"
        )

    logging.error(
        "Agent '%s' returned unexpected type: %s. Value: %r",
        agent.name, type(content).__name__, content,
    )
    raise TypeError(
        f"{agent.name} returned unexpected type {type(content).__name__}: {content!r}"
    )