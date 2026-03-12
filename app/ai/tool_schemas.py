"""Anthropic SDK tool definitions for all Itilite travel domain tools.

These schemas are passed to the Claude API on every chat turn so Claude
knows which tools are available and how to call them.
"""

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_trips",
        "description": "List upcoming and past trips for an employee. Use this when the user asks to see their trips, travel history, or upcoming travel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee's unique ID.",
                },
                "status": {
                    "type": "string",
                    "enum": ["upcoming", "past", "all"],
                    "description": "Filter trips by status. Default is 'all'.",
                },
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "get_trip_details",
        "description": "Get the full itinerary for a specific trip including all flight, hotel, and car rental segments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID (e.g. TRP-001).",
                },
            },
            "required": ["trip_id"],
        },
    },
    {
        "name": "create_booking",
        "description": "Initiate a booking request for a flight, hotel, or car rental on an existing trip.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID to attach this booking to.",
                },
                "segment_type": {
                    "type": "string",
                    "enum": ["flight", "hotel", "car"],
                    "description": "Type of segment to book.",
                },
                "option_id": {
                    "type": "string",
                    "description": "The inventory option ID selected by the traveler.",
                },
                "traveler_notes": {
                    "type": "string",
                    "description": "Optional notes from the traveler (seat preference, meal, etc.).",
                },
            },
            "required": ["trip_id", "segment_type", "option_id"],
        },
    },
    {
        "name": "get_booking",
        "description": "Retrieve the current status and full details of a specific booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID (e.g. BKG-F01).",
                },
            },
            "required": ["booking_id"],
        },
    },
    {
        "name": "cancel_booking",
        "description": "Cancel a booking and get the estimated refund amount and timeline.",
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
        "name": "get_travel_policy",
        "description": "Retrieve the company's travel policy rules for a specific category (flights, hotels, car, per_diem, general).",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_id": {
                    "type": "string",
                    "description": "The company ID.",
                },
                "category": {
                    "type": "string",
                    "enum": ["flights", "hotels", "car", "per_diem", "general"],
                    "description": "Policy category to retrieve.",
                },
            },
            "required": ["company_id", "category"],
        },
    },
    {
        "name": "check_policy_compliance",
        "description": "Validate whether a proposed booking amount and type complies with the company travel policy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_id": {
                    "type": "string",
                    "description": "The company ID.",
                },
                "segment_type": {
                    "type": "string",
                    "enum": ["flight", "hotel", "car"],
                    "description": "Type of booking segment.",
                },
                "amount": {
                    "type": "number",
                    "description": "The booking cost amount.",
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (e.g. INR, USD). Default: USD.",
                },
                "travel_class": {
                    "type": "string",
                    "description": "Travel class for flights (economy, business, etc.). Optional.",
                },
            },
            "required": ["company_id", "segment_type", "amount"],
        },
    },
    {
        "name": "search_faq",
        "description": "Search the Itilite platform FAQ for answers about how to use the platform, policies, and processes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_expense_report",
        "description": "Retrieve submitted expense reports for a specific trip.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "string",
                    "description": "The trip ID.",
                },
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID.",
                },
            },
            "required": ["trip_id", "employee_id"],
        },
    },
    {
        "name": "get_approval_status",
        "description": "Check the approval workflow status for a trip or booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The trip or booking ID.",
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["trip", "booking"],
                    "description": "Whether this is a trip or booking approval.",
                },
            },
            "required": ["entity_id", "entity_type"],
        },
    },
]
