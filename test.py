# test_chat.py  (run from project root)
import asyncio
import socketio

sio = socketio.AsyncClient()

# Signals that the namespace is fully registered and safe to emit on
_ns_ready = asyncio.Event()

@sio.event
async def connect():
    print("Connected.")
    _ns_ready.set()

@sio.on("session_info")
async def on_session(data):
    print("Session:", data["session_id"])
    # Wait until 'connect' has fired (namespace registered) before emitting.
    # If connect fired first, this returns immediately.
    await _ns_ready.wait()
    await sio.emit("send_message", {"content": "what is the weather forecast for new york this week?"})

@sio.on("error")
async def on_error(data):
    print("Server error:", data)

@sio.on("message")
async def on_message(data):
    print(f"\n[{data['role']}] {data['content']}")
    if data["role"] == "assistant":
        await sio.disconnect()

async def main():
    await sio.connect("http://localhost:8000")
    await sio.wait()

asyncio.run(main())
