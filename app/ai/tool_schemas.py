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
        "description": (
            "Cancel a hotel booking. "
            "Always call get_trip_itinerary first and confirm with the user "
            "before cancelling. "
            "Pass the 'Leg Request ID (use for cancel)' from the itinerary — "
            "do NOT pass the 'Ref Booking ID'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "leg_request_id": {
                    "type": "string",
                    "description": (
                        "24-character hex leg request ID from the itinerary "
                        "(hotels.legs[].leg_request_id). "
                        "Example: '69550d32aa90f845ff7e527f'. "
                        "Do NOT use booking_id here."
                    ),
                },
            },
            "required": ["leg_request_id"],
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
        "name": "cancel_car_booking",
        "description": (
            "Cancel a rental car booking. "
            "Always call get_trip_itinerary first and confirm with the user "
            "before cancelling. "
            "Pass the 'Service Master ID (use for cancel)' and "
            "'Car ID (use for cancel)' from the itinerary car leg."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service_master_id": {
                    "type": "integer",
                    "description": (
                        "Integer service master ID from the itinerary car leg "
                        "(cars.legs[].service_master_id). Example: 100502."
                    ),
                },
                "cab_id": {
                    "type": "integer",
                    "description": (
                        "Integer car/cab ID from the itinerary car leg "
                        "(cars.legs[].car_id). Example: 100807."
                    ),
                },
            },
            "required": ["service_master_id", "cab_id"],
        },
    },
]
