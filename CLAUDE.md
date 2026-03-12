# Itilite Travel Assistant — Developer PRD

## What We're Building

Itilite Travel Assistant is the AI-powered chat backend for the **Itilite corporate travel platform**.
Employees interact via a real-time Socket.IO chat interface. An AI assistant (Claude claude-sonnet-4-6)
handles their travel requests — querying trips, managing bookings, checking weather,
and more — via a set of domain tools.

A parallel **FastMCP server** (`mcp_server/server.py`, named `"itilite"`) exposes the same tools
for direct Claude Code / Claude Desktop integration.

---

## Domain Concepts

| Term | Definition |
|---|---|
| **Trip** | A travel event with purpose, dates, and destination. Contains one or more Segments. |
| **Segment** | One leg of a trip: a flight, hotel stay, or car rental. |
| **Booking** | A confirmed or pending reservation for a Segment. |
| **Policy** | Company-defined rules: max hotel nightly rate, flight class, per diem limits. |
| **Approval** | Multi-step workflow required for trips exceeding a cost threshold. |
| **Employee** | The traveler. Identified by `employee_id`. |
| **Company** | The employer. Identified by `company_id`. Owns the Policy. |

---

## Architecture

```
app/
├── ai/
│   ├── client.py        Claude API tool-use loop — chat_turn(session) -> str
│   ├── prompts.py       SYSTEM_PROMPT for the travel assistant persona
│   └── tool_schemas.py  Tool definitions in Anthropic SDK format
├── tools/
│   ├── __init__.py      exports TOOL_REGISTRY, dispatch
│   ├── registry.py      TOOL_REGISTRY dict + dispatch(tool_name, input)
│   ├── itinerary.py     get_trip_itinerary
│   ├── trips.py         get_trips_by_user
│   ├── hotels.py        get_hotel_details, cancel_hotel_booking, modify_hotel_booking
│   └── weather.py       get_weather_alerts, get_weather_forecast
├── services/
│   └── http_client.py   make_get_request, make_post_request, make_put_request
├── config.py            All settings — Anthropic API key, Claude model, Itilite API URLs
├── main.py              FastAPI + Socket.IO ASGI app
├── models.py            Pydantic: Message, Session, ToolCall
└── socket_manager.py    Socket.IO events; calls chat_turn() on each user message
mcp_server/
└── server.py            FastMCP("itilite") — registers tools from TOOL_REGISTRY
main.py                  Uvicorn entrypoint (port 8000)
```

**Single source of truth for tool logic:** `app/tools/` handlers are used by both
`app/ai/client.py` (via `dispatch`) and `mcp/server.py` (via `TOOL_REGISTRY`).
Tool schemas for the Anthropic API live in `app/ai/tool_schemas.py`.

---

## Tool-Use Loop

```
User message
  → Claude API (model + SYSTEM_PROMPT + full session history + TOOL_SCHEMAS)
  → stop_reason == "tool_use"
      → dispatch tool calls via app/tools/registry.py
      → append tool results as user turn
      → re-call Claude
  → stop_reason == "end_turn"
      → return text content → emit as assistant message over Socket.IO
```

---

## Tools Reference

| Name | Module | Description |
|---|---|---|
| `get_trip_itinerary` | itinerary.py | Full itinerary for a trip — flights, hotels, fare, traveller, amenities |
| `get_trips_by_user` | trips.py | List trips for a user, filterable by status |
| `get_hotel_details` | hotels.py | Static details for a hotel |
| `cancel_hotel_booking` | hotels.py | Cancel a hotel booking |
| `modify_hotel_booking` | hotels.py | Modify dates, room type, or special requests |
| `get_weather_alerts` | weather.py | Active NWS weather alerts for a US state |
| `get_weather_forecast` | weather.py | 5-period weather forecast by lat/lon |

---

## Environment

- Python 3.11, `uv` for package management
- `ANTHROPIC_API_KEY` in `.env` — **never commit `.env`**
- Model: `claude-sonnet-4-6`
- Chat server port: `8000`

---

## Current Status / Known Gaps

- [ ] **Session storage is in-memory** — replace `sessions` dict with Redis or DB
- [ ] **No auth on Socket.IO** — add JWT validation in the `connect` event handler
- [ ] **No streaming** — `chat_turn()` returns complete text; add streaming for UX
- [ ] **Employee/company context** — should come from auth token, not be passed by Claude

---

## Common Commands

```bash
uv run python main.py          # start chat server on :8000
mcp dev mcp_server/server.py   # start MCP dev inspector
uv add <package>               # add a dependency
uv sync                        # install all declared dependencies
curl http://localhost:8000/health   # health check
```
