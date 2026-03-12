"""Anthropic SDK tool definitions for real Itilite tools."""

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_upcoming_trips",
        "description": (
            "Fetch the user's upcoming trips (up to 10, sorted by "
            "journey date asc). "
            "Call this whenever the user asks about their trips without "
            "providing a trip_id — e.g. 'what trips do I have?', "
            "'cancel today's hotel', 'show me tomorrow's trip', "
            "'what's my next flight?'. "
            "Returns a summary table with trip_id, title, dates "
            "(with today/tomorrow labels), status, destination, and "
            "booking types. "
            "After showing the list, call get_trip_itinerary on the "
            "relevant trip_id before taking any action."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
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
        "description": (
            "Get static details for a booked hotel — amenities, "
            "description, room features, bedding, and photos. "
            "Call get_trip_itinerary first to get the required IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "leg_request_id": {
                    "type": "string",
                    "description": (
                        "24-char hex leg request ID from the itinerary "
                        "(hotels.legs[].leg_request_id)."
                    ),
                },
                "hotel_unique_id": {
                    "type": "string",
                    "description": (
                        "UUID-style hotel unique ID from the itinerary "
                        "(hotels.legs[].id)."
                    ),
                },
                "room_id": {
                    "type": "string",
                    "description": (
                        "Optional room ID "
                        "(hotels.legs[].room_details[0].id)."
                    ),
                },
                "auth_token": {
                    "type": "string",
                    "description": (
                        "Bearer token for authentication. "
                        "Pass the same token used for get_trip_itinerary."
                    ),
                },
                "trip_id": {
                    "type": "string",
                    "description": (
                        "Trip ID (e.g. '0653-1241'). Used to derive the "
                        "client-id header required by the hotel details API."
                    ),
                },
            },
            "required": ["leg_request_id", "hotel_unique_id", "trip_id"],
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
        "name": "get_flight_cancellation_details",
        "description": "Get cancellation eligibility, refund estimates, and eligible legs for a trip's flight bookings. Use this before attempting any flight cancellation so the user can review charges and confirm.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID (e.g. '0600-1241').",
                },
            },
            "required": ["trip_id"],
        },
    },
    {
        "name": "submit_flight_cancellation",
        "description": "Submit a flight cancellation request for specified legs. IMPORTANT: Only call this AFTER the user has reviewed cancellation details (from get_flight_cancellation_details) and explicitly confirmed they want to proceed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID (e.g. '0600-1241').",
                },
                "leg_request_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of leg_request_id values to cancel (from the cancellation details output).",
                },
            },
            "required": ["trip_id", "leg_request_ids"],
        },
    },
    {
        "name": "get_flight_cancellation_status",
        "description": "Check the status of a previously submitted flight cancellation request. Cancellations can take time to process, so use this to poll for updates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cancellation_request_id": {
                    "type": "string",
                    "description": "The cancellation request ID returned by submit_flight_cancellation.",
                },
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID (e.g. '0600-1241').",
                },
            },
            "required": ["cancellation_request_id", "trip_id"],
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
    {
        "name": "cancel_entire_trip",
        "description": (
            "Cancel ALL active legs of a trip — flights, hotels, and "
            "rental cars — in a single operation. "
            "Use this when the user explicitly asks to cancel their whole "
            "trip or 'everything' on a trip. "
            "Always call get_trip_itinerary first so you can show the user "
            "what will be cancelled (flights, hotels, cars), present any "
            "cancellation charges, and get explicit confirmation before "
            "calling this tool. "
            "Do NOT call individual cancel tools alongside this one — "
            "this tool handles all modes concurrently."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": (
                        "The trip ID to cancel entirely "
                        "(e.g. '0653-0070')."
                    ),
                },
            },
            "required": ["trip_id"],
        },
    },
]
