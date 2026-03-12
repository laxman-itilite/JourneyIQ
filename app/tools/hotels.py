import logging

from config import API_BASE_URL, ENDPOINTS
from services import make_get_request, make_post_request, make_put_request

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


async def cancel_hotel_booking(booking_id: str, reason: str = "") -> str:
    """Cancel a hotel booking.

    Args:
        booking_id: The booking ID to cancel (e.g. "BKG789")
        reason: Optional reason for cancellation
    """
    endpoint = ENDPOINTS["hotel_cancel"].format(booking_id=booking_id)
    url = f"{API_BASE_URL}{endpoint}"
    payload: dict = {"booking_id": booking_id}
    if reason:
        payload["reason"] = reason

    data = await make_post_request(url, payload)

    if not data:
        return f"Unable to process cancellation for booking '{booking_id}'."

    return str(data)


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


def register_hotel_tools(mcp) -> None:
    """Register all hotel-related tools."""
    mcp.tool()(get_hotel_details)
    mcp.tool()(cancel_hotel_booking)
    mcp.tool()(modify_hotel_booking)
