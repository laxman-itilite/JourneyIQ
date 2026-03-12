import os
from dotenv import load_dotenv

load_dotenv()

# ── Anthropic ─────────────────────────────────────────────────────────────────

def get_anthropic_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    return key

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096
TOOL_USE_MAX_ITERATIONS = 10

# ── Itilite API ───────────────────────────────────────────────────────────────

API_BASE_URL = "https://stream-api-qa.iltech.in"
HOTEL_STATIC_BASE_URL = "https://fast-api-qa.iltech.in"
USER_AGENT = "Itilite-TravelAssistant/1.0"
REQUEST_TIMEOUT = 30.0

ENDPOINTS = {
    "itinerary": "/api/v1/dashboard/itinerary/{trip_id}",
    "hotel_room_details": "/v1/hotel-room-details",
    "trips": "/trips",
    "hotel_cancel": "/hotels/{booking_id}/cancel",
    "hotel_modify": "/hotels/{booking_id}/modify",
    "hotel_static": "/hotels/{hotel_id}",
}

USER_ACCESS_TOKEN = os.environ.get("USER_ACCESS_TOKEN", "")
