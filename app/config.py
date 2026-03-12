import base64
import json
import os
from dotenv import load_dotenv, dotenv_values

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
    "flight_cancellation_details": "/v1/trip-modify/cancellation-details",
    "flight_cancellation_request": "/v1/trip-modify/cancellation-request",
}

def get_user_access_token() -> str:
    """Read USER_ACCESS_TOKEN fresh from .env each call.

    This means you can update the token in .env without restarting the server.
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczNDQyODgwLCJqdGkiOiIyYzhiZTcxMmU2Nzc0NDFhYjVhNWYzZTRhMTllZTYyNCIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.e8hTD6rkS6dnYEflvgAIHqtDMD5Oozo8-TwnnDyYMLSHBLDmbIu62ekIJrG26sbBKqqH41XthmY0NtrEEyhcFj28ZgBFhshBgIIj7AkAVxL15CFdFZDOPWkXqPxqWuWIwp7-_uEyMphN0OT-oB0lPnP7KQ4-1xH8JlqK3L98yntWysUF-mDogqNW5EmYU4UUnPVWv78xm0Djv0AFQqOIBs39Me-1DRRJh06EavR7z0K5cmkO5CBQtb5gpLb6khSS_RFBHRlAJ78nc66n_iiUv7jbDZenb0VSdCzj686WV8VxZ6Tz72ySlUWYAe8Fmwrh9-Z7KHGu0oEXJYNTdp77A_iCw2TGF7Gp0pBGSY8sTZv59v2bf9tXD3zQ1HYkdDh-UxAy0qPcSNOTUVjLpT-1vtZYH5_NG5NexIjveglfzGzmuW4_WqMYY77PPjVTUtB97anuIUEWbchdS_HLnzt9jox698lTpdp-JSPM11omBoQ5xz4qJ6EgRmvze9RVuoT6Ls984mdoXrZGMCDwzxe_PduVz1Zx9fPXxayvNAio9nTdDjzOjA_8hbM5eghQdSeU04XzZPNwrRgRg2hT-eOExhJcUcmg_8qhnENH7VYG10sQF4FcpUsKguE7Ii5x3G2mT50aEqtAD7T6DqVcWxJzqrn0ATCpGjDv2n3_YkfByF0"
    # env = dotenv_values()
    # return env.get("USER_ACCESS_TOKEN") or os.environ.get("USER_ACCESS_TOKEN", "")


def get_current_user_id() -> str:
    """Decode the JWT access token and return the user_id claim."""
    token = get_user_access_token()
    if not token:
        return ""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("user_id", "")
    except Exception:
        return ""
