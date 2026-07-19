# Pathy-RoadMap-AI

CLI tool that builds personalized learning roadmaps. Takes a topic, finds YouTube creators → their courses → community reviews → ranks them → generates a week-by-week roadmap with YouTube resources.

## Commands

```bash
uv run python cli.py start   # run the full pipeline (interactive prompts)
uv run python server.py      # start the FastAPI / AgentOS server
uv run pytest                 # run tests (none exist yet — only __init__.py)
```

`main.py` is a backward-compat shim for `cli.py` — use `cli.py` directly.

## Setup

- Python 3.12, package manager is `uv`
- `.env` is required (gitignored). Copy `.env.example` and fill in:
  - `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL_NAME` — any OpenAI-compatible API
  - `JINA_AI_KEY` — used for web search via `s.jina.ai` and page reading via `r.jina.ai`
- `DATABASE_URL` and `REDIS_URL` in `.env.example` are **not used** in code

## Architecture

```
cli.py:start() → ask_requirement() → _run_pipeline()
  → discover_creators()   (agents/creators.py)  — YouTube search → LLM → 3-5 creators
  → find_courses()        (agents/courses.py)   — YouTube→page URLs→LLM → course candidates
  → validate_reviews()    (agents/reviews.py)   — Reddit search → LLM → review evidence
  → rank_courses()        (agents/ranking.py)   — LLM scores courses (weighted rubric)
  → build_roadmap()       (agents/roadmap.py)   — LLM plans weeks → concurrent YouTube resource selection

server.py (FastAPI / AgentOS)
  → POST /api/generate   — direct REST API running the pipeline above
  → AgentOS endpoint     — serves `pathy-roadmap-agent` with `generate_learning_roadmap` tool
```

Output lands in `output/` as `.md` + `.json`. Logs go to `logs/production.log` (realtime flush).

## Agent system (agno 2.x)

- All agents built via `build_agent()` in `agents/base.py`
- Uses `OpenAILike` model (compatible with any OpenAI API)
- `use_json_mode=True`, `markdown=False` — pipeline agents emit JSON
- `pathy-roadmap-agent` in `server.py` uses `markdown=False` with `use_json_mode=True` (default builder configuration) but acts as a standard chat agent to stream/display tool outputs
- `response_content()` handles parsing: pydantic model, dict, JSON string, strips `</think>` blocks and markdown fences
- Agents are secured with `PromptInjectionGuardrail` to block instruction bypass attempts
- Agents with tool access (reviews, resources, server roadmap tool) use `agno.tools.function.Function` or direct tool definitions with `entrypoint` kwarg or standard signatures

## Key config (`utils/settings.py`)

`max_creators=5`, `max_courses=8`, `max_reviews_per_course=3`, `max_resource_candidates=3` — tunable via env.

## Conventions

- Web search uses Jina AI (`s.jina.ai`), YouTube search uses `youtube-search`, page reading uses Jina Reader (`r.jina.ai`)
- Course search explicitly **excludes** Udemy, DataCamp, Coursera, generic marketplaces
- Agent output schemas use wrapper types (`CreatorList`, `CourseCandidateList`, etc.) not bare lists — pydantic validation
- `save_markdown()` auto-creates `output/` dir
- No lint/formatter/typecheck config in repo
