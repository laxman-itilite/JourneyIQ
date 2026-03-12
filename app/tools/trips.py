"""Trip-related tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json


async def get_trips(employee_id: str, status: str = "all") -> str:
    """List trips for an employee filtered by status."""
    # TODO: call Itilite trips API
    mock_trips = [
        {
            "trip_id": "TRP-001",
            "title": "Client Visit - Mumbai",
            "destination": "Mumbai, India",
            "start_date": "2026-03-20",
            "end_date": "2026-03-22",
            "status": "upcoming",
            "purpose": "Client meeting",
            "total_cost": 15400.00,
            "currency": "INR",
        },
        {
            "trip_id": "TRP-002",
            "title": "Annual Conference - Bangalore",
            "destination": "Bangalore, India",
            "start_date": "2026-04-10",
            "end_date": "2026-04-12",
            "status": "upcoming",
            "purpose": "Conference",
            "total_cost": 22000.00,
            "currency": "INR",
        },
        {
            "trip_id": "TRP-003",
            "title": "Sales Review - Delhi",
            "destination": "Delhi, India",
            "start_date": "2026-02-15",
            "end_date": "2026-02-16",
            "status": "past",
            "purpose": "Internal meeting",
            "total_cost": 8500.00,
            "currency": "INR",
        },
    ]

    if status != "all":
        mock_trips = [t for t in mock_trips if t["status"] == status]

    if not mock_trips:
        return f"No {status} trips found for employee {employee_id}."

    return json.dumps({"employee_id": employee_id, "trips": mock_trips}, indent=2)


async def get_trip_details(trip_id: str) -> str:
    """Get full itinerary for a specific trip."""
    # TODO: call Itilite trip details API
    if trip_id != "TRP-001":
        return json.dumps({"error": f"Trip {trip_id} not found."})

    mock_detail = {
        "trip_id": "TRP-001",
        "title": "Client Visit - Mumbai",
        "status": "upcoming",
        "segments": [
            {
                "segment_id": "SEG-001",
                "type": "flight",
                "booking_id": "BKG-F01",
                "from": "Delhi (DEL)",
                "to": "Mumbai (BOM)",
                "departure": "2026-03-20T06:00:00",
                "arrival": "2026-03-20T08:15:00",
                "carrier": "IndiGo",
                "flight_number": "6E-201",
                "class": "Economy",
                "status": "confirmed",
                "cost": 4800.00,
            },
            {
                "segment_id": "SEG-002",
                "type": "hotel",
                "booking_id": "BKG-H01",
                "property": "Taj Lands End",
                "city": "Mumbai",
                "check_in": "2026-03-20",
                "check_out": "2026-03-22",
                "room_type": "Deluxe",
                "status": "confirmed",
                "cost_per_night": 5300.00,
                "nights": 2,
            },
            {
                "segment_id": "SEG-003",
                "type": "flight",
                "booking_id": "BKG-F02",
                "from": "Mumbai (BOM)",
                "to": "Delhi (DEL)",
                "departure": "2026-03-22T19:00:00",
                "arrival": "2026-03-22T21:10:00",
                "carrier": "Air India",
                "flight_number": "AI-131",
                "class": "Economy",
                "status": "confirmed",
                "cost": 5300.00,
            },
        ],
        "total_cost": 15400.00,
        "currency": "INR",
        "approval_status": "approved",
    }
    return json.dumps(mock_detail, indent=2)
