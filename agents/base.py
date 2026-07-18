import logging
from typing import get_origin, get_args
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from pydantic import BaseModel, create_model

from utils.settings import settings


def build_agent(
    name: str,
    instructions: list[str],
    output_schema=None,
    tools: list | None = None,
) -> Agent:
    logging.info(
        "Building agent: '%s' with model '%s', output_schema '%s', instructions count %d, tools %s",
        name,
        settings.OPENAI_MODEL_NAME,
        output_schema.__name__ if hasattr(output_schema, "__name__") else str(output_schema),
        len(instructions),
        [getattr(t, "name", str(t)) for t in tools] if tools else []
    )

    agent = Agent(
        name=name,
        model=OpenAILike(
            id=settings.OPENAI_MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        ),
        instructions=instructions,
        tools=tools or [],
        output_schema=output_schema,
        markdown=False,
        use_json_mode=True,
    )
    return agent


def response_content(agent: Agent, prompt: str):
    logging.info("Running agent '%s'. Prompt length: %d chars", agent.name, len(prompt))
    try:
        response = agent.run(prompt)
    except Exception as e:
        logging.error("Agent '%s' execution failed: %s", agent.name, str(e), exc_info=True)
        raise e

    if response.content is None:
        msg = f"{agent.name} returned an empty response."
        logging.error(msg)
        raise RuntimeError(msg)

    logging.info("Agent '%s' execution succeeded. Response length: %d chars", agent.name, len(str(response.content)))

    if agent.output_schema is not None and isinstance(response.content, str):
        print(f"\n[ERROR] {agent.name} failed to parse response into schema. Raw response:\n{response.content}\n")

    return response.content