# TODO: replace with actual base URL
API_BASE_URL = "https://api.journeyiq.com"
USER_AGENT = "JourneyIQ-MCP/1.0"
REQUEST_TIMEOUT = 30.0

# API Endpoints — update paths as APIs are confirmed
ENDPOINTS = {
    "itinerary": "/trips/{trip_id}/itinerary",
    "trips": "/trips",
    "hotel_cancel": "/hotels/{booking_id}/cancel",
    "hotel_modify": "/hotels/{booking_id}/modify",
    "hotel_static": "/hotels/{hotel_id}",
}
