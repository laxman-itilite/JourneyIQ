import logging

import app.config as _config
from app.config import CAR_SERVICE_BASE_URL, ENDPOINTS
from app.services import make_post_request

logger = logging.getLogger(__name__)


async def cancel_car_booking(
    service_master_id: int,
    cab_id: int,
) -> str:
    """Cancel a rental car booking.

    IMPORTANT — always follow this sequence:
    1. Call get_trip_itinerary to retrieve the itinerary.
    2. Show the user the car details and confirm they want to cancel.
    3. Get explicit user confirmation before proceeding.
    4. Pass service_master_id and cab_id from the itinerary.

    Both IDs are shown in the itinerary under the car leg:
      - service_master_id → "Service Master ID (use for cancel)"
      - cab_id            → "Car ID (use for cancel)"

    Args:
        service_master_id: Integer service master ID from the itinerary.
            Example: 100502
        cab_id: Integer car/cab ID from the itinerary.
            Example: 100807
    """
    auth_token = _config.get_user_access_token()
    url = f"{CAR_SERVICE_BASE_URL}{ENDPOINTS['car_cancel']}"
    headers = {"authorization": f"Bearer {auth_token}"}
    payload = {
        "service_master_id": service_master_id,
        "cab_cancellation_list": [{"cab_id": cab_id}],
    }

    data = await make_post_request(url, payload, headers=headers)

    if not data:
        return (
            f"❌ Car cancellation request failed for cab '{cab_id}'."
            " Please try again or contact support."
        )

    if data.get("status_code") == 200:
        return _format_car_cancel_success(data)

    msg = data.get("message") or "Unknown error"
    return (
        f"❌ Car cancellation failed for cab '{cab_id}'.\n"
        f"   Reason: {msg}"
    )


def _format_car_cancel_success(data: dict) -> str:
    """Format a successful car cancellation API response."""
    trip = data.get("trip_details", {})
    legs = data.get("cars", {}).get("legs", [])
    lines = ["✅ Car rental cancelled successfully."]

    if trip.get("trip_id"):
        lines.append(f"   Trip ID        : {trip['trip_id']}")
    if trip.get("status"):
        lines.append(f"   Trip Status    : {trip['status']}")

    for leg in legs:
        car = leg.get("car_details", {})
        vendor = car.get("vendor_name", "N/A")
        model = car.get("model_name", "N/A")
        lines += [
            f"   Car            : {vendor} — {model}",
            f"   Status         : {leg.get('status', 'N/A')}",
            f"   PNR            : {leg.get('pnr', 'N/A')}",
            f"   Cancelled At   : {leg.get('cancelled_at', 'N/A')}",
        ]
        pickup = leg.get("pickup", {})
        dropoff = leg.get("dropoff", {})
        if pickup.get("location"):
            lines.append(f"   Pick-up        : {pickup['location']}")
        if dropoff.get("location"):
            lines.append(f"   Drop-off       : {dropoff['location']}")
        fare = leg.get("fare", {})
        total = fare.get("total_price") or 0
        if total:
            c = fare.get("currency", "USD")
            lines.append(f"   Fare           : {c} {total:.2f}")
        if leg.get("voucher_link"):
            lines.append(f"   Voucher        : {leg['voucher_link']}")

    lines.append(
        "\n   Please allow a few minutes for the cancellation"
        " to reflect in your trip."
    )
    return "\n".join(lines)
