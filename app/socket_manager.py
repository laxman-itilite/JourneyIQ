import socketio
import uuid
import logging
from .models import Message, Session, ToolCall

logger = logging.getLogger(__name__)


def _truncate(text: str, max_chars: int = 4096) -> str:
    """Truncate text to max_chars, appending a marker if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 20] + "\n... [truncated]"

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

# In-memory store: session_id -> Session
sessions: dict[str, Session] = {}

# Map socket id -> session_id
socket_to_session: dict[str, str] = {}


def get_or_create_session(session_id: str | None) -> Session:
    if session_id and session_id in sessions:
        return sessions[session_id]
    new_id = session_id or str(uuid.uuid4())
    session = Session(id=new_id)
    sessions[new_id] = session
    return session


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None):
    session_id = (auth or {}).get("session_id")
    session = get_or_create_session(session_id)
    socket_to_session[sid] = session.id
    await sio.enter_room(sid, session.id)
    logger.info("Client %s connected, session %s", sid, session.id)
    await sio.emit(
        "session_info",
        {
            "session_id": session.id,
            "history": [m.model_dump() for m in session.messages],
        },
        to=sid,
    )


@sio.event
async def disconnect(sid: str):
    session_id = socket_to_session.pop(sid, None)
    logger.info("Client %s disconnected, session %s", sid, session_id)


@sio.event
async def send_message(sid: str, data: dict):
    """
    Client sends: { "content": "Hello" }
    Server emits back:
      - "message" (user echo) to the room
      - "message" (assistant reply) to the room  [placeholder until AI is wired in]
    """
    session_id = socket_to_session.get(sid)
    if not session_id or session_id not in sessions:
        await sio.emit("error", {"message": "Session not found"}, to=sid)
        return

    content = (data.get("content") or "").strip()
    if not content:
        await sio.emit("error", {"message": "Empty message"}, to=sid)
        return

    session = sessions[session_id]

    # Persist and broadcast the user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=content,
    )
    session.messages.append(user_msg)
    await sio.emit("message", user_msg.model_dump(), room=session_id)

    # Call AI and get structured response envelope
    reply = await generate_reply(session)

    # Convert raw tool call dicts to ToolCall models (truncate outputs)
    raw_tool_calls = reply.get("tool_calls") or []
    tool_call_models = [
        ToolCall(
            id=tc["id"],
            name=tc["name"],
            input=tc["input"],
            output=_truncate(tc.get("output") or ""),
        )
        for tc in raw_tool_calls
    ]

    # Build assistant message — store plain text in `content` (no JSON envelopes)
    # and tool_calls for context on follow-up turns.
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=reply["content"],
        tool_calls=tool_call_models,
        buttons=reply.get("buttons") or [],
        connect_to_human=reply.get("connect_to_human", False),
        modification_requested=reply.get("modification_requested", False),
        summary=reply.get("summary") or "",
    )
    session.messages.append(assistant_msg)
    await sio.emit("message", assistant_msg.model_dump(), room=session_id)

    if assistant_msg.connect_to_human or assistant_msg.modification_requested:
        from app.tools.email import send_support_email
        from app.config import get_current_user_id
        request_type = "modification" if assistant_msg.modification_requested else "support"
        await send_support_email(
            user_id=get_current_user_id(),
            summary=assistant_msg.summary,
            messages=session.messages,
            request_type=request_type,
        )


async def generate_reply(session: Session) -> dict:
    from app.ai.client import chat_turn
    return await chat_turn(session)
