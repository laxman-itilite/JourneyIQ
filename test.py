"""Interactive Socket.IO chat test client.

Usage:
    uv run python test.py
    python test.py

Type your message and press Enter. Ctrl+C or 'exit'/'quit' to quit.
"""
import asyncio
import sys
import socketio

sio = socketio.AsyncClient()

_ns_ready = asyncio.Event()
_response_ready = asyncio.Event()


@sio.event
async def connect():
    print("Connected to Itilite Travel Assistant.")
    _ns_ready.set()


@sio.event
async def disconnect():
    print("Disconnected.")


@sio.on("session_info")
async def on_session(data):
    print(f"Session: {data['session_id']}\n")


@sio.on("error")
async def on_error(data):
    print(f"Server error: {data}")
    _response_ready.set()


@sio.on("message")
async def on_message(data):
    if data["role"] == "assistant":
        print(f"\nAssistant: {data['content']}\n")
        _response_ready.set()


async def main():
    await sio.connect("http://localhost:8000")
    await _ns_ready.wait()

    print("Type your message (or 'exit' to quit):\n")

    loop = asyncio.get_event_loop()
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("You: ").strip())
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        _response_ready.clear()
        await sio.emit("send_message", {"content": user_input})
        await _response_ready.wait()

    await sio.disconnect()


asyncio.run(main())
