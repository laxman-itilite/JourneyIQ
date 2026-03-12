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
USER_AGENT = "JourneyIQ-MCP/1.0"
REQUEST_TIMEOUT = 30.0

ENDPOINTS = {
    "itinerary": "/api/v1/dashboard/itinerary/{trip_id}",
    "hotel_room_details": "/v1/hotel-room-details",
    "trips": "/trips",
    "hotel_cancel": "/hotels/{booking_id}/cancel",
    "hotel_modify": "/hotels/{booking_id}/modify",
    "hotel_static": "/hotels/{hotel_id}",
}

USER_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczMzE4ODc5LCJqdGkiOiI0MDVmMjNjYmNkMTU0YWNlOWI0MWVmOTg0MTdhNDRkNiIsInVzZXJfaWQiOiJGaWx1c0B5b3BtYWlsLmNvbSJ9.Xp_uyGhmLkGhXWSEm4-ki_LXESJTAL0SG7tzCl0FTkGk6280qmriREs-EuMl58Xs5GKztBivLOHFvmKC7-GPqq1whcNM1FBwr5-_kjEzWXSzlKY96Z31GEm8Vu3BQjZFve_ySL8b0UY3S898jkrCypBka2Qz_pezw7I1PWqJF261CmbrN7pDzBid1Dkh3ip0U9agdIuKHJ6Ano-2pr9enqcpJziwh0XZdWxrCzDRtIMiOt3xTlagkKQBuRcmQsysQ7nBAyw9iv8tzjoH_b6sRqrGXTxcf5DHaDGPLHC8l6VJXQr_c5gZkaLD-aKK0QChDGB2YHKqPpcUCobNZyrKlyATY7zZcWtylG33usO8rA7qJOYtrC8Hnr_5qPgg0pGUv4ErNegeCvrmtAgqbJenCrFW2_1UWVKSbN9yXOweRvTHluP5EUAdceVfVPVDthQ7-CQ7pKc8EDITcCm7b_58lEQTe2YWFN8N2cn8H5R1qcyAvKefcsYHkOweRHIxx4gfEjWiq57jrKmKNAKCn5PhbbyDDadSTJhxv6ShP_J5GrFUyOoTkxeaR2v7VPdKLiE4C1sPWvNW8MtwRKp6eLUd_SlsRZc9u68uBo2mhAGFMnPJrbriYIMNTVR3xm9o87BKcKioeUBxLPCE_LGoYFhwUbCLwMF7LIfsQs5vpSN9XhE"
