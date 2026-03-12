import logging

import app.config as _config
from app.config import API_BASE_URL, HOTEL_SERVICE_BASE_URL, ENDPOINTS
from app.services import make_get_request, make_post_request, make_put_request

logger = logging.getLogger(__name__)


async def get_hotel_details(hotel_id: str) -> str:
    """Get static details for a hotel.

    Args:
        hotel_id: The unique identifier for the hotel (e.g. "HTL456")
    """
    endpoint = ENDPOINTS["hotel_static"].format(hotel_id=hotel_id)
    url = f"{API_BASE_URL}{endpoint}"
    data = await make_get_request(url)

    if not data:
        return f"Unable to fetch details for hotel '{hotel_id}'."

    return str(data)


async def cancel_hotel_booking(leg_request_id: str) -> str:
    """Cancel a hotel booking.

    IMPORTANT — always follow this sequence:
    1. Call get_trip_itinerary to retrieve the itinerary.
    2. Show the user the cancellation policy and any charges.
    3. Get explicit user confirmation before cancelling.
    4. Pass the leg_request_id shown in the itinerary to this tool.

    The leg_request_id is a 24-character hex string shown in the itinerary
    as "Leg Request ID (use for cancel)".
    It looks like "69550d32aa90f845ff7e527f".

    DO NOT pass booking_id (e.g. "10019492491") — that is a different field
    labelled "Ref Booking ID" and will cause the cancellation to fail.

    Args:
        leg_request_id: 24-char hex leg request ID from the itinerary
            (hotels.legs[].leg_request_id). Example: "69550d32aa90f845ff7e527f"
    """
    auth_token = _config.get_user_access_token()
    url = f"{HOTEL_SERVICE_BASE_URL}{ENDPOINTS['hotel_cancel']}"
    headers = {"authorization": f"Bearer {auth_token}"}
    payload = {"legRequestIds": [leg_request_id]}

    data = await make_post_request(url, payload, headers=headers)

    if not data:
        return (
            f"❌ Cancellation request failed for leg '{leg_request_id}'."
            " Please try again or contact support."
        )

    if data.get("success"):
        inner = data.get("data", {})
        msg = inner.get("message", "")
        success_count = inner.get("successCount", 1)
        failure_count = inner.get("failureCount", 0)
        lines = [
            "✅ Hotel booking cancelled successfully.",
            f"   Leg Request ID : {leg_request_id}",
        ]
        if msg:
            lines.append(f"   Message        : {msg}")
        lines.append(
            f"   Cancellations  : {success_count} succeeded,"
            f" {failure_count} failed"
        )
        for result in inner.get("successResults", []):
            detail_parts = [
                p for p in [
                    result.get("roomId", ""),
                    result.get("message", ""),
                ]
                if p
            ]
            if detail_parts:
                lines.append(f"   Detail         : {' — '.join(detail_parts)}")
        ts = inner.get("timestamp") or data.get("timestamp", "")
        if ts:
            lines.append(f"   Timestamp      : {ts}")
        lines.append(
            "\n   Please allow a few minutes for the cancellation"
            " to reflect in your trip."
        )
        return "\n".join(lines)

    # Surface the error from the API
    inner = data.get("data", {})
    fail_results = inner.get("failureResults", [])
    reason = (
        fail_results[0].get("message", "")
        if fail_results
        else data.get("message", "Unknown error")
    )
    return (
        f"❌ Hotel cancellation failed for leg '{leg_request_id}'.\n"
        f"   Reason: {reason}"
    )


async def modify_hotel_booking(
    booking_id: str,
    new_check_in: str = "",
    new_check_out: str = "",
    new_room_type: str = "",
    special_requests: str = "",
) -> str:
    """Modify an existing hotel booking.

    Args:
        booking_id: The booking ID to modify (e.g. "BKG789")
        new_check_in: New check-in date YYYY-MM-DD (optional)
        new_check_out: New check-out date YYYY-MM-DD (optional)
        new_room_type: Room type e.g. "deluxe", "suite" (optional)
        special_requests: Any special requests (optional)
    """
    endpoint = ENDPOINTS["hotel_modify"].format(booking_id=booking_id)
    url = f"{API_BASE_URL}{endpoint}"
    payload: dict = {"booking_id": booking_id}
    if new_check_in:
        payload["new_check_in"] = new_check_in
    if new_check_out:
        payload["new_check_out"] = new_check_out
    if new_room_type:
        payload["new_room_type"] = new_room_type
    if special_requests:
        payload["special_requests"] = special_requests

    data = await make_put_request(url, payload)

    if not data:
        return f"Unable to process modification for booking '{booking_id}'."

    return str(data)
