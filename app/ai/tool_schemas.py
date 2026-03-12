"""Anthropic SDK tool definitions for real Itilite tools."""

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_trip_itinerary",
        "description": "Get the full itinerary for a specific trip including flights, hotels, fare breakdown, and traveller details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID (e.g. '0600-0621').",
                },
            },
            "required": ["trip_id"],
        },
    },
    # {
    #     "name": "get_trips_by_user",
    #     "description": "List all trips for the current user, optionally filtered by status.",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "status": {
    #                 "type": "string",
    #                 "enum": ["upcoming", "ongoing", "completed", "cancelled"],
    #                 "description": "Filter by trip status (optional).",
    #             },
    #         },
    #         "required": [],
    #     },
    # },
    {
        "name": "get_hotel_details",
        "description": "Get static details for a hotel by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_id": {
                    "type": "string",
                    "description": "The hotel's unique ID.",
                },
            },
            "required": ["hotel_id"],
        },
    },
    {
        "name": "cancel_hotel_booking",
        "description": "Cancel a hotel booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID to cancel.",
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for cancellation.",
                },
            },
            "required": ["booking_id"],
        },
    },
    {
        "name": "modify_hotel_booking",
        "description": "Modify an existing hotel booking's dates, room type, or special requests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID to modify.",
                },
                "new_check_in": {
                    "type": "string",
                    "description": "New check-in date YYYY-MM-DD (optional).",
                },
                "new_check_out": {
                    "type": "string",
                    "description": "New check-out date YYYY-MM-DD (optional).",
                },
                "new_room_type": {
                    "type": "string",
                    "description": "Room type e.g. 'deluxe', 'suite' (optional).",
                },
                "special_requests": {
                    "type": "string",
                    "description": "Any special requests (optional).",
                },
            },
            "required": ["booking_id"],
        },
    },
    {
        "name": "get_weather_alerts",
        "description": "Get active weather alerts for a US state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Two-letter US state code (e.g. CA, NY).",
                },
            },
            "required": ["state"],
        },
    },
    {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for a location by latitude and longitude.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude of the location.",
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude of the location.",
                },
            },
            "required": ["latitude", "longitude"],
        },
    },
]
