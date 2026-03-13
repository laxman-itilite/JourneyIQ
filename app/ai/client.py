"""Claude API client with tool-use loop.

Entry point: chat_turn(session) — runs one full user turn, executing any
tool calls Claude requests, and returns a structured response dict.
"""
import json
import re
import anthropic

from app.config import get_anthropic_api_key, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, TOOL_USE_MAX_ITERATIONS
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tool_schemas import TOOL_SCHEMAS
from app.tools.registry import dispatch

_FALLBACK_RESPONSE = {
    "content": "I was unable to complete that request.",
    "buttons": ["Try again"],
    "connect_to_human": False,
    "modification_requested": False,
    "tool_calls": [],
    "summary": "",
}

_TOOL_OUTPUT_CONTEXT_LIMIT = 4096

# Module-level lazy singleton — one HTTP connection pool per process
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=get_anthropic_api_key())
    return _client


def _build_messages(session) -> list[dict]:
    """Convert Session.messages to Anthropic API message format.

    For assistant messages that have tool_calls, a [Tool Context] block is
    appended so Claude can see what data was fetched in prior turns without
    needing to re-call tools.
    """
    result = []
    for msg in session.messages:
        content = msg.content
        if msg.role == "assistant" and msg.tool_calls:
            content = _append_tool_context(content, msg.tool_calls)
        result.append({"role": msg.role, "content": content})
    return result


def _append_tool_context(content: str, tool_calls: list) -> str:
    """Append a [Tool Context] summary to assistant message content."""
    lines = [content, "", "[Tool Context from this turn]"]
    for tc in tool_calls:
        input_str = json.dumps(tc.input, separators=(",", ":"))
        output = tc.output or ""
        if len(output) > _TOOL_OUTPUT_CONTEXT_LIMIT:
            output = output[:_TOOL_OUTPUT_CONTEXT_LIMIT - 20] + "\n... [truncated]"
        lines.append(f"- {tc.name}({input_str}): {output}")
    return "\n".join(lines)


def _parse_response(raw_text: str) -> dict:
    """Parse Claude's JSON response envelope.

    Claude is instructed to reply with a raw JSON object. This function
    handles several failure modes:
    1. Clean JSON (ideal) — parse directly.
    2. JSON wrapped in ```json fences — strip fences first.
    3. Plain text followed by a JSON code block — extract the JSON block.
    4. Plain text with no JSON — wrap as a paragraph fallback.

    Returns a dict with keys: content, buttons, connect_to_human.
    """
    text = raw_text.strip()

    # Attempt 1: parse the whole response as JSON
    data = _try_parse_json(text)
    if data is not None:
        return _extract_fields(data, raw_text)

    # Attempt 2: strip ```json ... ``` fences
    if text.startswith("```"):
        inner = _strip_fences(text)
        data = _try_parse_json(inner)
        if data is not None:
            return _extract_fields(data, raw_text)

    # Attempt 3: find a JSON code block anywhere in the response
    # (handles: plain text + ```json { ... } ```)
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        data = _try_parse_json(fence_match.group(1))
        if data is not None:
            return _extract_fields(data, raw_text)

    # Attempt 4: find the last top-level { ... } in the response
    last_brace = text.rfind("{")
    if last_brace != -1:
        candidate = text[last_brace:]
        data = _try_parse_json(candidate)
        if data is not None:
            return _extract_fields(data, raw_text)

    # Fallback: plain text, no JSON found
    return {
        "content": raw_text,
        "buttons": [],
        "connect_to_human": False,
        "modification_requested": False,
        "summary": "",
    }


def _try_parse_json(text: str) -> dict | None:
    """Try to parse text as JSON, return dict or None."""
    try:
        data = json.loads(text.strip())
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from around content."""
    lines = text.splitlines()
    if lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return "\n".join(lines[1:]).strip()


def _extract_fields(data: dict, raw_text: str) -> dict:
    """Pull the expected fields from a parsed JSON dict."""
    return {
        "content": data.get("content", raw_text),
        "buttons": data.get("buttons") or [],
        "connect_to_human": bool(data.get("connect_to_human", False)),
        "modification_requested": bool(data.get("modification_requested", False)),
        "summary": data.get("summary") or "",
    }


async def chat_turn(session) -> dict:
    """Run one full user turn through Claude, including the tool-use loop.

    Algorithm:
    1. Build message list from session history (all prior user+assistant turns).
       Note: session messages store only the plain text from the `content` field so
       Claude sees clean conversation history, not raw JSON envelopes.
    2. Call Claude with TOOL_SCHEMAS.
    3. If stop_reason == "tool_use":
       a. Collect all tool_use content blocks.
       b. Execute each via dispatch(), collect results.
       c. Append assistant turn (with tool_use blocks) to local message list.
       d. Append user turn (with tool_result blocks) to local message list.
       e. Re-call Claude (up to TOOL_USE_MAX_ITERATIONS).
    4. When stop_reason == "end_turn": parse JSON envelope and return structured dict.

    Args:
        session: Session object with .messages list of Message objects.

    Returns:
        Structured dict with keys: content, buttons, connect_to_human, tool_calls.
    """
    client = _get_client()
    messages = _build_messages(session)
    collected_tool_calls: list[dict] = []

    for _ in range(TOOL_USE_MAX_ITERATIONS):
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    parsed = _parse_response(block.text)
                    parsed["tool_calls"] = collected_tool_calls
                    return parsed
            fallback = dict(_FALLBACK_RESPONSE)
            fallback["tool_calls"] = collected_tool_calls
            return fallback

        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Append assistant message (contains tool_use blocks — must be kept as SDK objects
            # so the SDK can serialise them correctly in the next API call)
            messages.append({"role": "assistant", "content": response.content})

            # Execute all requested tools in sequence and collect results
            tool_results = []
            for tool_use in tool_use_blocks:
                result_text = await dispatch(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result_text,
                })
                collected_tool_calls.append({
                    "id": tool_use.id,
                    "name": tool_use.name,
                    "input": tool_use.input,
                    "output": result_text,
                })

            # Append tool results as a user turn
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason (max_tokens, stop_sequence, etc.)
        break

    return _FALLBACK_RESPONSE
