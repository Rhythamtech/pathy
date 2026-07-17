from agno.agent import Agent
from agno.models.openai.like import OpenAILike

from utils.settings import settings


def build_agent(
    name: str,
    instructions: list[str],
    output_schema=None,
    tools: list | None = None,
) -> Agent:
    return Agent(
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
    )


def response_content(agent: Agent, prompt: str):
    response = agent.run(prompt)
    return response.content