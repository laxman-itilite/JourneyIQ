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
HOTEL_SERVICE_BASE_URL = "https://hotel-qa.iltech.in"
CAR_SERVICE_BASE_URL = "https://service-qa.iltech.in"
USER_AGENT = "Itilite-TravelAssistant/1.0"
REQUEST_TIMEOUT = 30.0

ENDPOINTS = {
    "itinerary": "/api/v1/dashboard/itinerary/{trip_id}",
    "hotel_room_details": "/v1/hotel-room-details",
    "trips": "/trips",
    "upcoming_trips": (
        "/api/v1/traveler/dashboard/business/itinerary/upcoming"
    ),
    "hotel_cancel": "/service/hotel/cancel/hotel-cancellation",
    "hotel_modify": "/hotels/{booking_id}/modify",
    "hotel_static": "/hotels/{hotel_id}",
    "flight_cancellation_details": "/v1/trip-modify/cancellation-details",
    "flight_cancellation_request": "/v1/trip-modify/cancellation-request",
    "car_cancel": "/api/v2/cab/rental_car/cancel_booking",
}

def get_user_access_token() -> str:
    """Read USER_ACCESS_TOKEN fresh from .env each call.

    This means you can update the token in .env without restarting the server.
    """
    # return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczNDQyODgwLCJqdGkiOiIyYzhiZTcxMmU2Nzc0NDFhYjVhNWYzZTRhMTllZTYyNCIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.e8hTD6rkS6dnYEflvgAIHqtDMD5Oozo8-TwnnDyYMLSHBLDmbIu62ekIJrG26sbBKqqH41XthmY0NtrEEyhcFj28ZgBFhshBgIIj7AkAVxL15CFdFZDOPWkXqPxqWuWIwp7-_uEyMphN0OT-oB0lPnP7KQ4-1xH8JlqK3L98yntWysUF-mDogqNW5EmYU4UUnPVWv78xm0Djv0AFQqOIBs39Me-1DRRJh06EavR7z0K5cmkO5CBQtb5gpLb6khSS_RFBHRlAJ78nc66n_iiUv7jbDZenb0VSdCzj686WV8VxZ6Tz72ySlUWYAe8Fmwrh9-Z7KHGu0oEXJYNTdp77A_iCw2TGF7Gp0pBGSY8sTZv59v2bf9tXD3zQ1HYkdDh-UxAy0qPcSNOTUVjLpT-1vtZYH5_NG5NexIjveglfzGzmuW4_WqMYY77PPjVTUtB97anuIUEWbchdS_HLnzt9jox698lTpdp-JSPM11omBoQ5xz4qJ6EgRmvze9RVuoT6Ls984mdoXrZGMCDwzxe_PduVz1Zx9fPXxayvNAio9nTdDjzOjA_8hbM5eghQdSeU04XzZPNwrRgRg2hT-eOExhJcUcmg_8qhnENH7VYG10sQF4FcpUsKguE7Ii5x3G2mT50aEqtAD7T6DqVcWxJzqrn0ATCpGjDv2n3_YkfByF0"
    # env = dotenv_values()
    # return env.get("USER_ACCESS_TOKEN") or os.environ.get("USER_ACCESS_TOKEN", "")
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczNDU0OTI5LCJqdGkiOiJmZjdlM2NhOWQ4NzA0YjUxYTc3NGU4MDg5N2IyNjQ5YSIsInVzZXJfaWQiOiJweXRob253YWxsQHlvcG1haWwuY29tIn0.c3yu7VdZJL38yR1-ehcggVVY0yYPJhSgkpzd4djXU_qe2X-I4ndK8OU8YiVvR7G766y2mJIyIVc6my6q-8POOEZNuBPkocjKIixkFd8a1TyYrzfyOpR8QOpaZOrqeg389JlNKRP-tDjgBSF8DY9g0oyf7m4NajcOhwk5wpw8xuQSJ-KAGX5ipR6ZN1xtJPF0FJXkPM_JF_he4rHsNU84oH5aguTMa4T6GFUdxz8kWEKrvcg-K_ikE1A4b1DKKqpyhNNC7aK9-X4iimh9sKnaDEbjBTmHC3cBs5zBS7ZppL2cQ9fbUAOJKBUfNb2L8js1M451Z2uev0GsW7QzVAJ4LeRDAWoF_11c2e6DGMcyqwOYcXPg1PmSSfq9mkbhpBWvJeeSxHuduxmfOQpcES58rhFpfUPlzcTIha92nc6zqns9oKegzNGbqK8bfk2boOTAW8o38M617Z0XrvV8DOTvec0QfCuvh3SltUTcCRNMj1GRUIxOuy5iRqjNjZa2nseF1Qx33GHHt-EIYHwE6bQQfnByJsBPpkFwJKxn_jN2JS1J0OYX6qi5ka7ZNN9TMEvlx7-PnALK0plj4k9Tvtq76wVtBCPnEnNRh6W6iTe2fNNPxfVfseToDR8xFvldiXE-66cYJd6cyeDevP-eaEi3_Vzt0ZAagHttkL7jilLZUyM"
    # return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczNDk5MTQyLCJqdGkiOiJkNTVkZWQyZjJmYzY0MTgwOWU2YmU1YThiYWNjZDgwNyIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.GkD7ujiiacesHXO8FhHk5AOeH7Xafd5CbTe9feUsCKMsjC0sYozRNbvz3b63u3PlQNn42WSxHBVNQlIzOjABqffVmBLZPwzN6L-KZcJmO9fvQv7dqT7h_L1rENcTuci5IefdaYjNtDkqNZjzAAA4UzGfHF0Uw-fVbUhi9E80flOxX7ivZ8WEqbRD7Ts85CuAtbz_SlaXLVPg0MsY3XyBmdwfl8n5CHY1pbUO6StoU7QAxe7H0ZMbOyKIHD2UBsL4hJxFjS01gbNWirvZVPJc4m5zm60eRdGvytfG1swl7rl9GLwlbTZpbgfp8C844m_2st4z_lYnH9ECFmK6Er2j0PANuvy3H0Vh4iR4PveaK33H8Gcdk4A3OTSNl4yc6mMe_SKNLck3_mJcdKqu2FjIBHUHsshei3I4TnvXEFBaS3suK3qlPGPHyTbPNgeaXx34aiA8N94STuwtrpdeHTfpniPAarZ7CS9llgSTIjno0OesKVkDVwl6N1VcYsCx_zmcZh36-qncsyDWf6TgnRSQyV1WWjh1J0bOvuXYhyKqP473GAEIiE5pYSi5gJh-Aqfx2df5rPDNqJGrCs_iLtXJ-fztNYY3bGAh8k2iwusGYZP6CJY-mkTmTtELD2JbdHfQEaOp77fZFHhaiGVKPSRW9Ns_aa7wsxCz3wrJSFD6Xd8"

# ── Email ─────────────────────────────────────────────────────────────────────

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support-itilite@yopmail.com")


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
