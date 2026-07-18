"""
Tests for agents/base.py — specifically _extract_json and response_content.
These tests are pure-unit: no network, no LLM, no .env required.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

# Patch settings before any import that touches it
with patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "http://localhost",
        "OPENAI_MODEL_NAME": "test-model",
        "JINA_AI_KEY": "test-jina",
    },
):
    from agents.base import _extract_json, response_content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Simple(BaseModel):
    name: str
    value: int


def _make_agent(schema=_Simple):
    """Return a minimal mock agent with the given output_schema."""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.output_schema = schema
    return agent


def _make_response(content):
    resp = MagicMock()
    resp.content = content
    return resp


# ---------------------------------------------------------------------------
# _extract_json
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_plain_json(self):
        raw = '{"name": "Alice", "value": 42}'
        assert _extract_json(raw) == raw

    def test_strips_markdown_json_fence(self):
        raw = '```json\n{"name": "Bob", "value": 1}\n```'
        result = _extract_json(raw)
        assert result == '{"name": "Bob", "value": 1}'

    def test_strips_plain_code_fence(self):
        raw = '```\n{"name": "Carol", "value": 2}\n```'
        result = _extract_json(raw)
        assert result == '{"name": "Carol", "value": 2}'

    def test_strips_leading_text_before_brace(self):
        raw = 'Here is the JSON:\n{"name": "Dan", "value": 3}'
        result = _extract_json(raw)
        assert result == '{"name": "Dan", "value": 3}'

    def test_strips_trailing_text_after_brace(self):
        # This is the "Extra data" scenario fixed in base.py
        raw = '{"name": "Eve", "value": 4} some trailing garbage'
        result = _extract_json(raw)
        assert result == '{"name": "Eve", "value": 4}'

    def test_strips_think_block(self):
        raw = '<think>Some reasoning here</think>\n{"name": "Frank", "value": 5}'
        result = _extract_json(raw)
        assert result == '{"name": "Frank", "value": 5}'

    def test_strips_think_block_and_trailing(self):
        raw = '<think>reasoning</think>{"name": "Grace", "value": 6}extra'
        result = _extract_json(raw)
        assert result == '{"name": "Grace", "value": 6}'

    def test_no_braces_returns_empty_string(self):
        result = _extract_json("no json here at all")
        assert result == "no json here at all"  # falls back to stripped text

    def test_empty_string(self):
        assert _extract_json("") == ""

    def test_whitespace_only(self):
        assert _extract_json("   ") == ""

    def test_nested_json_preserved(self):
        raw = '{"outer": {"inner": 99}}'
        result = _extract_json(raw)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"] == 99


# ---------------------------------------------------------------------------
# response_content
# ---------------------------------------------------------------------------

class TestResponseContent:
    @pytest.mark.asyncio
    async def test_returns_schema_instance_directly(self):
        """If the agent already returns a Pydantic model, pass it through."""
        agent = _make_agent()
        instance = _Simple(name="Alice", value=1)
        agent.arun = AsyncMock(return_value=_make_response(instance))

        result = await response_content(agent, "prompt")
        assert result is instance

    @pytest.mark.asyncio
    async def test_parses_json_string(self):
        """If agent returns a raw JSON string, parse it into the schema."""
        agent = _make_agent()
        agent.arun = AsyncMock(
            return_value=_make_response('{"name": "Bob", "value": 2}')
        )

        result = await response_content(agent, "prompt")
        assert isinstance(result, _Simple)
        assert result.name == "Bob"
        assert result.value == 2

    @pytest.mark.asyncio
    async def test_parses_json_string_with_trailing_garbage(self):
        """Trailing content after `}` must not crash the parser."""
        agent = _make_agent()
        agent.arun = AsyncMock(
            return_value=_make_response('{"name": "Carol", "value": 3} \nDone.')
        )

        result = await response_content(agent, "prompt")
        assert isinstance(result, _Simple)
        assert result.name == "Carol"

    @pytest.mark.asyncio
    async def test_parses_dict_content(self):
        """If agent returns a dict, construct the schema from it."""
        agent = _make_agent()
        agent.arun = AsyncMock(
            return_value=_make_response({"name": "Dan", "value": 4})
        )

        result = await response_content(agent, "prompt")
        assert isinstance(result, _Simple)
        assert result.value == 4

    @pytest.mark.asyncio
    async def test_raises_on_empty_response(self):
        agent = _make_agent()
        agent.arun = AsyncMock(return_value=_make_response(None))

        with pytest.raises(RuntimeError, match="empty response"):
            await response_content(agent, "prompt")

    @pytest.mark.asyncio
    async def test_raises_on_unparseable_string(self):
        agent = _make_agent()
        agent.arun = AsyncMock(
            return_value=_make_response("this is not json at all")
        )

        with pytest.raises(RuntimeError, match="failed to parse"):
            await response_content(agent, "prompt")

    @pytest.mark.asyncio
    async def test_no_schema_returns_raw_content(self):
        """With output_schema=None the raw content is returned as-is."""
        agent = _make_agent(schema=None)
        agent.arun = AsyncMock(return_value=_make_response("raw text"))

        result = await response_content(agent, "prompt")
        assert result == "raw text"

    @pytest.mark.asyncio
    async def test_raises_on_unexpected_type(self):
        agent = _make_agent()
        agent.arun = AsyncMock(return_value=_make_response(12345))  # int, not valid

        with pytest.raises(TypeError, match="unexpected type"):
            await response_content(agent, "prompt")
