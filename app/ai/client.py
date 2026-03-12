"""Claude API client with tool-use loop.

Entry point: chat_turn(session) — runs one full user turn, executing any
tool calls Claude requests, and returns a structured response dict.
"""
import json
import anthropic

from app.config import get_anthropic_api_key, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, TOOL_USE_MAX_ITERATIONS
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tool_schemas import TOOL_SCHEMAS
from app.tools.registry import dispatch

_FALLBACK_RESPONSE = {
    "content": "I was unable to complete that request. Please try again.",
    "buttons": [],
    "connect_to_human": False,
}

# Module-level lazy singleton — one HTTP connection pool per process
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=get_anthropic_api_key())
    return _client


def _build_messages(session) -> list[dict]:
    """Convert Session.messages to Anthropic API message format.

    Only user/assistant text turns are stored in the session (tool call turns
    are ephemeral within a single chat_turn invocation). This keeps session
    storage simple while still giving Claude the full conversation history.
    """
    return [{"role": msg.role, "content": msg.content} for msg in session.messages]


def _parse_response(raw_text: str) -> dict:
    """Parse Claude's JSON response envelope.

    Claude is instructed to always reply with a JSON object. This function
    extracts the JSON (stripping any accidental markdown fences), then
    validates the expected fields. Falls back gracefully if parsing fails.

    Returns a dict with keys: content, buttons, connect_to_human.
    """
    text = raw_text.strip()
    # Strip ```json ... ``` fences if Claude wraps the JSON
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = inner.strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # Claude replied with plain text instead of JSON — wrap it
        return {
            "content": raw_text,
            "buttons": [],
            "connect_to_human": False,
        }

    return {
        "content": data.get("content", raw_text),
        "buttons": data.get("buttons") or [],
        "connect_to_human": bool(data.get("connect_to_human", False)),
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
        Structured dict with keys: content, buttons, connect_to_human.
    """
    client = _get_client()
    messages = _build_messages(session)

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
                    return _parse_response(block.text)
            return _FALLBACK_RESPONSE

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

            # Append tool results as a user turn
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason (max_tokens, stop_sequence, etc.)
        break

    return _FALLBACK_RESPONSE
