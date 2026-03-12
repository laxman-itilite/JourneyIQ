from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timezone


class Message(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class Session(BaseModel):
    id: str
    created_at: str = ""
    messages: list[Message] = []

    def model_post_init(self, __context):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
