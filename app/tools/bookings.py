"""Booking tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json
import uuid
from datetime import datetime, timezone


async def create_booking(trip_id: str, segment_type: str, option_id: str, traveler_notes: str = "") -> str:
    """Initiate a booking for a flight, hotel, or car on a trip."""
    # TODO: call Itilite booking creation API
    booking_id = f"BKG-{uuid.uuid4().hex[:6].upper()}"
    mock_booking = {
        "booking_id": booking_id,
        "trip_id": trip_id,
        "segment_type": segment_type,
        "option_id": option_id,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": f"Booking request submitted. Awaiting manager approval.",
        "traveler_notes": traveler_notes,
    }
    return json.dumps(mock_booking, indent=2)


async def get_booking(booking_id: str) -> str:
    """Get status and details of a booking."""
    # TODO: call Itilite booking details API
    mock_bookings = {
        "BKG-F01": {
            "booking_id": "BKG-F01",
            "type": "flight",
            "trip_id": "TRP-001",
            "from": "Delhi (DEL)",
            "to": "Mumbai (BOM)",
            "departure": "2026-03-20T06:00:00",
            "carrier": "IndiGo 6E-201",
            "class": "Economy",
            "status": "confirmed",
            "pnr": "ABCD12",
            "cost": 4800.00,
            "currency": "INR",
            "cancellation_deadline": "2026-03-18T06:00:00",
        },
        "BKG-H01": {
            "booking_id": "BKG-H01",
            "type": "hotel",
            "trip_id": "TRP-001",
            "property": "Taj Lands End, Mumbai",
            "check_in": "2026-03-20",
            "check_out": "2026-03-22",
            "room_type": "Deluxe",
            "status": "confirmed",
            "confirmation_number": "TAJ-98765",
            "cost": 10600.00,
            "currency": "INR",
            "free_cancellation_until": "2026-03-19T12:00:00",
        },
    }
    booking = mock_bookings.get(booking_id)
    if not booking:
        return json.dumps({"error": f"Booking {booking_id} not found."})
    return json.dumps(booking, indent=2)
