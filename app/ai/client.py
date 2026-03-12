"""Claude API client with tool-use loop.

Entry point: chat_turn(session) — runs one full user turn, executing any
tool calls Claude requests, and returns the final assistant text.
"""
import anthropic

from app.config import get_anthropic_api_key, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, TOOL_USE_MAX_ITERATIONS
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tool_schemas import TOOL_SCHEMAS
from app.tools.registry import dispatch

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


async def chat_turn(session) -> str:
    """Run one full user turn through Claude, including the tool-use loop.

    Algorithm:
    1. Build message list from session history (all prior user+assistant turns).
    2. Call Claude with TOOL_SCHEMAS.
    3. If stop_reason == "tool_use":
       a. Collect all tool_use content blocks.
       b. Execute each via dispatch(), collect results.
       c. Append assistant turn (with tool_use blocks) to local message list.
       d. Append user turn (with tool_result blocks) to local message list.
       e. Re-call Claude (up to TOOL_USE_MAX_ITERATIONS).
    4. When stop_reason == "end_turn": extract and return the text block.

    Args:
        session: Session object with .messages list of Message objects.

    Returns:
        Assistant reply as a plain string.
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
                    return block.text
            return ""

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

    return "I was unable to complete that request. Please try again."
