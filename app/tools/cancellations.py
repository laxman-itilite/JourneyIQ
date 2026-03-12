"""Cancellation tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json
from datetime import datetime, timezone


async def cancel_booking(booking_id: str, reason: str = "") -> str:
    """Cancel a booking and return estimated refund information."""
    # TODO: call Itilite cancellation API
    mock_cancellations = {
        "BKG-F01": {
            "booking_id": "BKG-F01",
            "type": "flight",
            "original_cost": 4800.00,
            "cancellation_fee": 1500.00,
            "refund_amount": 3300.00,
            "currency": "INR",
            "refund_eta_days": 7,
        },
        "BKG-H01": {
            "booking_id": "BKG-H01",
            "type": "hotel",
            "original_cost": 10600.00,
            "cancellation_fee": 0.00,
            "refund_amount": 10600.00,
            "currency": "INR",
            "refund_eta_days": 3,
            "note": "Free cancellation applies — cancelled before deadline.",
        },
    }

    info = mock_cancellations.get(booking_id)
    if not info:
        return json.dumps({"error": f"Booking {booking_id} not found or already cancelled."})

    result = {
        **info,
        "status": "cancelled",
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason or "Not specified",
        "message": f"Booking {booking_id} cancelled. Refund of {info['currency']} {info['refund_amount']:.2f} will be processed in {info['refund_eta_days']} business days.",
    }
    return json.dumps(result, indent=2)
