# Itilite JourneyIQ — Developer PRD

## What We're Building

JourneyIQ is the AI-powered chat backend for the **Itilite corporate travel platform**.
Employees interact via a real-time Socket.IO chat interface. An AI assistant (Claude claude-sonnet-4-6)
handles their travel requests — querying trips, managing bookings, checking cancellations,
answering policy questions, and searching the FAQ — via a set of domain tools.

A parallel **FastMCP server** (`mcp/server.py`, named `"itilite"`) exposes the same tools
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
│   ├── registry.py      dispatch(tool_name, input) — routes Claude tool calls to handlers
│   ├── trips.py         get_trips, get_trip_details
│   ├── bookings.py      create_booking, get_booking
│   ├── cancellations.py cancel_booking
│   ├── policy.py        get_travel_policy, check_policy_compliance
│   ├── faq.py           search_faq
│   ├── expenses.py      get_expense_report
│   └── approvals.py     get_approval_status
├── config.py            Settings — loads .env, exposes ANTHROPIC_API_KEY
├── main.py              FastAPI + Socket.IO ASGI app
├── models.py            Pydantic: Message, Session, ToolCall
└── socket_manager.py    Socket.IO events; calls chat_turn() on each user message
mcp/
└── server.py            FastMCP("itilite") — wraps app/tools/ handlers for MCP surface
main.py                  Uvicorn entrypoint (port 8000)
```

**Single source of truth for tool logic:** `app/tools/` handlers are imported by both
`app/ai/client.py` (for the chat backend) and `mcp/server.py` (for the MCP server).
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
| `get_trips` | trips.py | List upcoming/past trips for employee |
| `get_trip_details` | trips.py | Full itinerary for a trip |
| `create_booking` | bookings.py | Book flight/hotel/car on a trip |
| `get_booking` | bookings.py | Booking status and details |
| `cancel_booking` | cancellations.py | Cancel a booking, get refund estimate |
| `get_travel_policy` | policy.py | Company policy rules by category |
| `check_policy_compliance` | policy.py | Validate booking against policy |
| `search_faq` | faq.py | Search Itilite FAQ |
| `get_expense_report` | expenses.py | Expense reports for a trip |
| `get_approval_status` | approvals.py | Approval workflow status |

---

## Environment

- Python 3.11, `uv` for package management
- `ANTHROPIC_API_KEY` in `.env` — **never commit `.env`**
- Model: `claude-sonnet-4-6`
- Chat server port: `8000`

---

## Current Status / Known Gaps

- [ ] **Tools are stubs** — replace stub return values with real Itilite API calls
- [ ] **Session storage is in-memory** — replace `sessions` dict with Redis or DB
- [ ] **No auth on Socket.IO** — add JWT validation in the `connect` event handler
- [ ] **No streaming** — `chat_turn()` returns complete text; add streaming for UX
- [ ] **Employee/company context** — currently hardcoded in stubs; should come from auth token

---

## Common Commands

```bash
uv run python main.py          # start chat server on :8000
mcp dev mcp/server.py          # start MCP dev inspector
uv add <package>               # add a dependency
uv sync                        # install all declared dependencies
curl http://localhost:8000/health   # health check
```
