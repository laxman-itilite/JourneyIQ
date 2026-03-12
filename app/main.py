import socketio
from fastapi import FastAPI
from .socket_manager import sio

fastapi_app = FastAPI(title="JourneyIQ Chat API")


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


# Mount Socket.IO under /socket.io (default path)
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
