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
USER_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczMzIyNjk5LCJqdGkiOiJlNGY3OGVkZWZkMGU0ODA3OTFmZjVjMDRkNTRiOTBlMyIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.yeiObuy5_JR6Wvq_BK_Et7RhE_VBX3_lNXZDdiCR2y0kCMNbEwDa1OZ8IrTSNuQsbIZNZI2Nu6LRlKPq4bPDGr8PHyM3aFozuOECdHV-ME8Vvi3N23O1Ecpumxbufz-nZ9JN3WQMC6Pg8lv-XshER2r1thhu_ttChC_o1D6KudkrzyDdT3A057_Fnir8lWVR2E-U-pIYgq6o8zRIF-Hgd-ztF7GaItUXL5QX5WQONiJmHFiT19_CqA4_tMaSnMyICvsTx_ILum6lX-uSIygcscCrUIEeZFBc6BhZed2M9a6n1qHHVjZpvWSM2AU9Rb02aI6zgcNXMwYvwC0bRgV-kw3ip9guhWuOE15C3b4JUPWERL32jLwY_oc_pRGIilfT8bFBBhznZEhj43t1pTaVBrPvff64lXobFkhviAAdsQK4apKijlUs9rE1q9DYSRyggMWmjcuHHv9gV4V9Ig8-mrkH4zNNmu0a4QCPZfn9F20mBARAs3kup4LuOnnxF-ElRFUiXiqEpLAp31NnG_6XZQYqnulLshED5qf2K8yyK4qVYXq32aQOiTpwqPNWaHzeL61O8OMfvz-XY0UoqRrwLETALLBWBOErocQq29hA1ss4UhekjXKXvujNn9lIjN6yhyKzxfAdrLPngDnIagnkrasZ5NGEcCuHzDmb9EfGvGU"
