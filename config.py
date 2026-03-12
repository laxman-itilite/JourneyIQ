# TODO: replace with actual base URL
API_BASE_URL = "https://stream-api-qa.iltech.in"
HOTEL_STATIC_BASE_URL = "https://fast-api-qa.iltech.in"
USER_AGENT = "JourneyIQ-MCP/1.0"
REQUEST_TIMEOUT = 30.0

# API Endpoints
ENDPOINTS = {
    "itinerary": "/api/v1/dashboard/itinerary/{trip_id}",
    "hotel_room_details": "/v1/hotel-room-details",
    "trips": "/trips",
    "hotel_cancel": "/hotels/{booking_id}/cancel",
    "hotel_modify": "/hotels/{booking_id}/modify",
    "hotel_static": "/hotels/{hotel_id}",
}
