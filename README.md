# Itilite Travel Assistant

AI-powered chat backend for the [Itilite](https://www.itilite.com) corporate travel platform. Employees chat in real time and an AI assistant handles trip queries, bookings, cancellations, policy questions, and FAQs.

## Stack

- **Python 3.11** + [uv](https://docs.astral.sh/uv/)
- **FastAPI** + **python-socketio** — real-time chat over Socket.IO
- **Anthropic Claude** (`claude-sonnet-4-6`) — AI with tool use
- **FastMCP** — MCP server (`"itilite"`) for Claude Code / Claude Desktop integration

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set your API key
cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY

# 3. Start the chat server
uv run python main.py
# → http://localhost:8000
# → Socket.IO at ws://localhost:8000/socket.io
```

## MCP Server (Claude Desktop / Claude Code)

```bash
mcp dev mcp/server.py
```

The MCP server is named `"itilite"` and exposes all 10 travel domain tools.

## Socket.IO Events

| Direction | Event | Payload |
|---|---|---|
| client → server | `send_message` | `{ content: "show my trips" }` |
| server → client | `message` | `Message` object (role: user \| assistant) |
| server → client | `session_info` | `{ session_id, history: Message[] }` |
| server → client | `error` | `{ message: "..." }` |

Connect with optional auth to resume a session:
```js
const socket = io("http://localhost:8000", { auth: { session_id: "existing-id" } })
```

## Project Structure

```
app/ai/          Claude API client + prompts + tool schemas
app/tools/       Travel domain tool handlers (stubs → real Itilite API)
mcp/server.py    FastMCP "itilite" server
app/socket_manager.py   Socket.IO event handlers
```

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
