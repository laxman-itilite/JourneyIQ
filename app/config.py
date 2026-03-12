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

# USER_ACCESS_TOKEN = os.environ.get("USER_ACCESS_TOKEN", "")
USER_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczMzIzMDAxLCJqdGkiOiJjOTgyMWIxMDk4YmQ0NGZjOWMxMjBjNmI1Y2ExZTJkZSIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.dwo4P2c27xxTgQvA-TZ_9kNB0DOHNLyiuMMtd4MJioxFG_IFZBRJ6tqSGsZu993GeJob1b165WBmVFsbmdrqwPII41zK81AKjiXfkC2ITMkNsphMZubnhg7mSULtN5zT_viIlqwuAt96Ucos5UfS8cbOkJ2unKYn1rs9NuYUVucrWIH0Qg59aP-aB1Pm1yW_yFnWPxshwMxQWtcOg2wdr2YmrJadVOAexwPpXDQj2LDpEfbgLq_dQ4IO88qhNPLF0i6Pd0JUlfjyPiCa8QDTtNOx1OgNwOVgEKHlTX7y_MRaAbH_78GhAWz_Dqm_2dQ84pd8jiY6gKDacp2ntp28dwiRzbuTCv3CgZQqB8TNt9ZmjFpaxw2DSnlpCeh2AEzK0UQvzwG39hFJorTZvkXQys8MPQkG5MkKV1Kcua7oVLjML4uZufft_YPcMO0klBFSIoOrYOXFgDvwiTGrmuIsMFEa1K4R0y4GCr684a2FiE9dJe8491MQWttecHhrguEC8bIe5ZXMBppZ_eFvbTk0G9XjT6IR1vlmH0h_Dpa6CTNC3UedDiKEVpl4Xh5EZteDgiuYBnH2Bjne_EsHA-dkUhhIn9ays2z6CGYKe3iCLiy84v1uJJrV_A4fIdA3tNojztZjQUoZR0TlU69R5UJ9BQbDE-rLqrc_8pAwx6Y6QWc"
