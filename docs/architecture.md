# JourneyIQ — Architecture & End-to-End Working

## Bird's Eye View

```
Frontend (browser / mobile app)
    ↕  Socket.IO  (ws://localhost:8000)
FastAPI + Socket.IO Server  (main.py → app/main.py)
    ↕  Python function call
Claude API (Anthropic claude-sonnet-4-6)  ←→  Tool handlers (app/tools/)
    ↕  HTTPS
Itilite Backend APIs  (stream-api-qa.iltech.in)
```

---

## Project Structure

```
JourneyIQ/
├── main.py                    # Uvicorn entry point (port 8000)
├── app/
│   ├── main.py                # FastAPI + Socket.IO ASGI app
│   ├── config.py              # Settings: API keys, URLs, token
│   ├── models.py              # Pydantic: Message, Session, ToolCall
│   ├── socket_manager.py      # Socket.IO event handlers
│   ├── services.py            # HTTP helpers (make_get/post/put_request)
│   ├── ai/
│   │   ├── client.py          # Claude tool-use loop → chat_turn()
│   │   ├── prompts.py         # SYSTEM_PROMPT (travel assistant persona)
│   │   └── tool_schemas.py    # Tool definitions in Anthropic SDK format
│   └── tools/
│       ├── registry.py        # dispatch(tool_name, input) → str
│       ├── itinerary.py       # get_trip_itinerary
│       ├── trips.py           # get_trips_by_user
│       ├── hotels.py          # get_hotel_details, cancel/modify booking
│       └── weather.py         # get_weather_alerts, get_weather_forecast
├── mcp/
│   └── server.py              # FastMCP("itilite") — dev/testing surface
├── test.py                    # Interactive Socket.IO chat test client
├── CLAUDE.md                  # Living PRD (auto-loaded by Claude Code)
└── .env                       # ANTHROPIC_API_KEY, etc. (never commit)
```

---

## Startup Sequence

```
uv run python main.py
```

1. `main.py` calls `uvicorn.run("app.main:app")`
2. `app/main.py` creates a **FastAPI** app and mounts a **Socket.IO** ASGI wrapper
3. `app/socket_manager.py` registers handlers: `connect`, `disconnect`, `send_message`
4. `app/config.py` runs `load_dotenv()` → reads `ANTHROPIC_API_KEY`, `USER_ACCESS_TOKEN`, and API base URLs from `.env`

---

## Connection Flow

```
Frontend                           Server
   │                                  │
   │── io("http://localhost:8000") ──▶│  HTTP upgrade → WebSocket
   │                                  │  connect handler fires:
   │                                  │  • create/retrieve Session (UUID)
   │                                  │  • map socket_id → session_id
   │                                  │  • join room(session_id)
   │◀── emit("session_info") ─────────│  { session_id, history: [] }
   │                                  │
```

To resume a previous session across reconnects:
```js
io("http://localhost:8000", { auth: { session_id: "existing-uuid" } })
```

---

## Message Flow

### 1. User sends a message

```js
socket.emit("send_message", { content: "show my trip 0600-0621" })
```

### 2. Server receives it (`socket_manager.py`)

```
send_message handler
  ├── look up session from socket_to_session map
  ├── create Message(role="user", content="...")
  ├── append to session.messages
  ├── emit("message", user_msg) → room   # frontend shows it immediately
  └── await generate_reply(session)      # calls chat_turn()
```

### 3. AI Loop (`app/ai/client.py` — `chat_turn()`)

```
session.messages → convert to Anthropic message format
        ↓
Claude API  (model + SYSTEM_PROMPT + TOOL_SCHEMAS + full history)
        ↓
┌─────────────────────────────────────────────┐
│  stop_reason == "tool_use"?                 │
│                                             │
│  YES → extract ToolUseBlock(s)              │
│      → dispatch each to app/tools/          │
│      → append assistant turn (tool_use)     │
│      → append user turn (tool_results)      │
│      → call Claude again  ──────────────────┤
│                                             │
│  NO (end_turn) → extract text → return ◀───┘
└─────────────────────────────────────────────┘
  max 10 iterations (guards against infinite loops)
```

### 4. Tool dispatch (`app/tools/registry.py`)

```python
dispatch("get_trip_itinerary", {"trip_id": "0600-0621"})
    → TOOL_REGISTRY["get_trip_itinerary"](**input)
    → itinerary.get_trip_itinerary(trip_id="0600-0621", auth_token=USER_ACCESS_TOKEN)
    → HTTP GET https://stream-api-qa.iltech.in/api/v1/dashboard/itinerary/0600-0621
    → formatted string result
```

`auth_token` is always injected from `config.USER_ACCESS_TOKEN` — the user never sees or provides it.

### 5. Response back to frontend

```
chat_turn() returns final text
    ↓
socket_manager creates Message(role="assistant", content=text)
    ↓
session.messages.append(assistant_msg)   # stored for conversation memory
    ↓
sio.emit("message", assistant_msg.model_dump(), room=session_id)
    ↓
Frontend receives: { role: "assistant", content: "Here is your trip..." }
```

---

## The 7 Tools

| Tool | Handler | API Called |
|---|---|---|
| `get_trip_itinerary` | `itinerary.py` | Itilite itinerary API + hotel static enrichment |
| `get_trips_by_user` | `trips.py` | Itilite trips API |
| `get_hotel_details` | `hotels.py` | Itilite hotel static API |
| `cancel_hotel_booking` | `hotels.py` | Itilite hotel cancel API |
| `modify_hotel_booking` | `hotels.py` | Itilite hotel modify API |
| `get_weather_alerts` | `weather.py` | NWS weather API |
| `get_weather_forecast` | `weather.py` | NWS weather API |

Tool schemas are defined in `app/ai/tool_schemas.py` (Anthropic SDK format). Handlers are registered in `app/tools/registry.py`. Both the chat backend and the MCP server share these handlers.

---

## Session Memory

Every message to Claude includes the **full conversation history** from `session.messages`.
This gives Claude multi-turn memory within a session:

```
You:        "show my trip 0600-0621"
Assistant:  "Here is your trip... Flight DEL→BOM, Hotel Taj Mumbai..."
You:        "cancel the hotel"
            ↑ Claude knows which hotel from context — no need to repeat trip ID
Assistant:  calls cancel_hotel_booking("BKG-H01")
```

> **Current limitation:** Sessions are in-memory. They survive reconnects (using `session_id`)
> but are lost on server restart. Replace the `sessions` dict with Redis or a DB for production.

---

## Authentication (Current State)

A hardcoded `USER_ACCESS_TOKEN` in `app/config.py` is used for all Itilite API calls.
This is injected as the default value of `auth_token` in tool handlers and is never exposed to Claude or the end user.

**Planned:** Replace with per-user JWT passed via Socket.IO auth on connect.

---

## MCP Server (Dev/Testing Only)

```
mcp dev mcp/server.py
```

`mcp/server.py` registers the same `TOOL_REGISTRY` handlers as MCP tools under the server name `"itilite"`. This lets you invoke tools directly from **Claude Desktop or Claude Code** for testing — without running the full chat server.

---

## Complete Data Flow

```
Browser
  │  emit("send_message", { content: "show my trip 0600-0621" })
  ▼
app/socket_manager.py
  │  store user message → session.messages
  │  await chat_turn(session)
  ▼
app/ai/client.py
  │  build Anthropic messages from session history
  │  POST api.anthropic.com/v1/messages
  │    system: SYSTEM_PROMPT
  │    tools:  TOOL_SCHEMAS
  │    model:  claude-sonnet-4-6
  ▼
Claude decides: call get_trip_itinerary(trip_id="0600-0621")
  ▼
app/tools/registry.py → dispatch()
  ▼
app/tools/itinerary.py → get_trip_itinerary()
  │  auth_token = USER_ACCESS_TOKEN  (from config)
  │  GET stream-api-qa.iltech.in/api/v1/dashboard/itinerary/0600-0621
  │  (+ parallel hotel static enrichment calls)
  ▼
Formatted itinerary string returned to Claude
  ▼
app/ai/client.py
  │  Claude processes tool result → generates final response
  │  stop_reason == "end_turn"
  ▼
app/socket_manager.py
  │  store assistant message → session.messages
  │  emit("message", { role: "assistant", content: "..." })
  ▼
Browser renders the response
```

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Authenticates requests to Claude API |

All other config (API URLs, token, model name) lives directly in `app/config.py`.

---

## Running the Project

```bash
# Start the chat server
uv run python main.py
# → http://localhost:8000
# → Socket.IO at ws://localhost:8000

# Interactive test client
uv run python test.py

# MCP dev server (optional)
mcp dev mcp/server.py

# Health check
curl http://localhost:8000/health
```
