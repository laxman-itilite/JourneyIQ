import logging

import app.config as _config
from app.config import (
    HOTEL_STATIC_BASE_URL,
    HOTEL_SERVICE_BASE_URL,
    API_BASE_URL,
    ENDPOINTS,
)
from app.services import make_post_request, make_put_request

logger = logging.getLogger(__name__)


def _client_id_from_trip(trip_id: str) -> str:
    """Extract client ID from trip ID prefix. e.g. '0653-1241' → '653'."""
    try:
        return str(int(trip_id.split("-")[0]))
    except (ValueError, IndexError):
        return ""


async def get_hotel_details(
    leg_request_id: str,
    hotel_unique_id: str,
    room_id: str = "",
    auth_token: str = "",
    trip_id: str = "",
) -> str:
    """Get static details for a booked hotel — amenities, description,
    room features, and photos.

    Both leg_request_id and hotel_unique_id are shown in the itinerary
    under each hotel leg. Call get_trip_itinerary first if you don't
    have them.

    Args:
        leg_request_id: 24-char hex leg request ID from the itinerary
            (hotels.legs[].leg_request_id).
        hotel_unique_id: UUID-style hotel unique ID from the itinerary
            (hotels.legs[].id).
        room_id: Optional room ID (hotels.legs[].room_details[0].id).
        auth_token: Bearer token for authentication.
        trip_id: Trip ID (e.g. '0653-1241') used to derive client-id header.
    """
    if not auth_token:
        auth_token = _config.get_user_access_token()
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['hotel_room_details']}"
    client_id = _client_id_from_trip(trip_id) if trip_id else ""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "role": "traveler",
        **({"client-id": client_id} if client_id else {}),
    }
    payload = {
        "mode": "hotel",
        "leg_details": {
            "leg_info_id": leg_request_id,
            "hotel_unique_id": hotel_unique_id,
            "room_id": room_id,
            "is_booked": True,
        },
    }

    data = await make_post_request(url, payload, headers=headers)

    if not data or data.get("status_code") != 200:
        return (
            f"Unable to fetch static details for hotel leg"
            f" '{leg_request_id}'."
        )

    static = data.get("response_data", {})
    return _format_hotel_static(static)


def _format_hotel_static(static: dict) -> str:
    """Format hotel static details (amenities, photos, room info)."""
    lines: list[str] = []

    name = static.get("hotel_name", "")
    if name:
        lines.append(f"🏨 {name}")

    # Property description
    desc = static.get("property_description", "").strip()
    if desc:
        lines.append("\n📋 Description:")
        words, buf = desc.split(), []
        for word in words:
            if sum(len(w) + 1 for w in buf) + len(word) > 72:
                lines.append("   " + " ".join(buf))
                buf = [word]
            else:
                buf.append(word)
        if buf:
            lines.append("   " + " ".join(buf))

    # Check-in / check-out times
    ci = static.get("check_in", "")
    co = static.get("check_out", "")
    if ci or co:
        lines.append(
            f"\n🕐 Check-in: {ci or 'N/A'}"
            f"  |  Check-out: {co or 'N/A'}"
        )

    # Property-level amenities
    prop_amenities = [
        a.get("amenity_name", "")
        for a in static.get("amenities", [])
        if a.get("amenity_name")
    ]
    if prop_amenities:
        lines.append("\n✨ Property Amenities:")
        lines.append("   " + ", ".join(prop_amenities))

    # Room details
    rooms = static.get("room_details", [])
    if rooms:
        sr = rooms[0]
        lines.append("\n🛏 Room Details:")

        bedding = [
            b.get("description", "")
            for b in sr.get("bedding", [])
            if b.get("description")
        ]
        if bedding:
            lines.append(f"   Bedding      : {', '.join(bedding)}")

        room_amenities = [
            a.get("name", "") for a in sr.get("amenities", [])
            if a.get("name")
        ]
        if room_amenities:
            lines.append(
                f"   Amenities    : {', '.join(room_amenities)}"
            )

        feats = [
            f"A/C {'✅' if sr.get('is_ac') else '❌'}",
            f"WiFi {'✅' if sr.get('is_wifi') else '❌'}",
            f"TV {'✅' if sr.get('is_tv') else '❌'}",
            f"Coffee {'✅' if sr.get('is_coffee') else '❌'}",
            f"Parking {'✅' if sr.get('parking_available') else '❌'}",
        ]
        if sr.get("airport_transfer_available"):
            feats.append("Airport Transfer ✅")
        lines.append(f"   Features     : {' | '.join(feats)}")

        sq_ft = sr.get("square_footage", 0)
        if sq_ft:
            lines.append(f"   Size         : {sq_ft} sq ft")

        # Photos — all of them for an explicit detail request
        photos = sr.get("photos", [])
        if photos:
            lines.append(f"\n📷 Photos ({len(photos)}):")
            for p in photos:
                lines.append(f"   {p}")

    if not lines:
        return "No static details available for this hotel."

    return "\n".join(lines)


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
