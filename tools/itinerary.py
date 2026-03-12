import logging

from mcp.server.fastmcp import FastMCP

from config import API_BASE_URL, ENDPOINTS
from services import make_get_request

logger = logging.getLogger(__name__)


def register_itinerary_tools(mcp: FastMCP) -> None:
    """Register all itinerary-related tools."""

    @mcp.tool()
    async def get_trip_itinerary(trip_id: str, auth_token: str) -> str:
        """Get the full itinerary for a specific trip including hotel,
        flight, fare and traveller details.

        Args:
            trip_id: The unique trip identifier (e.g. "0600-0621")
            auth_token: Bearer token for authentication
        """
        endpoint = ENDPOINTS["itinerary"].format(trip_id=trip_id)
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"authorization": f"Bearer {auth_token}"}
        response = await make_get_request(url, headers=headers)

        if not response or response.get("status_code") != 200:
            return f"Unable to fetch itinerary for trip '{trip_id}'."

        data = response.get("data", {})
        return _format_itinerary(data)


def _format_itinerary(data: dict) -> str:
    lines: list[str] = []

    # ── Trip Summary ─────────────────────────────────────────────────────────
    trip = data.get("trip_details", {})
    title = (
        trip.get("title", {}).get("trip")
        or trip.get("title", {}).get("default")
        or "N/A"
    )
    lines += [
        "═" * 50,
        f"🧳 TRIP: {title}",
        f"   ID          : {trip.get('trip_id', 'N/A')}",
        f"   Status      : {trip.get('status', 'N/A')}",
        f"   Destination : {trip.get('destination', 'N/A')}",
        f"   Dates       : {trip.get('min_date_utc', 'N/A')}"
        f" → {trip.get('max_date_utc', 'N/A')}",
    ]

    # ── Traveller ────────────────────────────────────────────────────────────
    user = data.get("user_details", {})
    lines += [
        "",
        "👤 TRAVELLER",
        f"   Name  : {user.get('full_name', 'N/A')}",
        f"   Email : {user.get('email', 'N/A')}",
        f"   Phone : {user.get('contact_no', 'N/A')}",
    ]

    # ── Fare Summary ─────────────────────────────────────────────────────────
    fare = data.get("fare", {})
    currency = fare.get("currency", "")
    lines += [
        "",
        "💰 FARE SUMMARY",
        f"   Total Price : {currency} {fare.get('total_price', 0):.2f}",
        f"   Paid        : {currency} {fare.get('total_paid', 0):.2f}",
        f"   To Be Paid  : {currency} {fare.get('to_be_paid', 0):.2f}",
        f"   Base Price  : {currency} {fare.get('base_price', 0):.2f}",
        f"   Tax         : {currency} {fare.get('tax', 0):.2f}",
    ]

    # ── Flights ──────────────────────────────────────────────────────────────
    flights = data.get("flights", {})
    if flights.get("count", 0) > 0:
        lines += ["", f"✈️  FLIGHTS ({flights['count']})"]
        for leg in flights.get("legs", []):
            lines.append(f"   • {leg}")
    else:
        lines += ["", "✈️  FLIGHTS: None"]

    # ── Hotels ───────────────────────────────────────────────────────────────
    hotels = data.get("hotels", {})
    hotel_legs = hotels.get("legs", [])
    lines += ["", f"🏨 HOTELS ({hotels.get('count', 0)})"]
    for i, leg in enumerate(hotel_legs, 1):
        h = leg.get("hotel_details", {})
        addr = h.get("address", {})
        room = leg.get("room_details", [{}])[0]
        leg_fare = leg.get("fare", {})
        leg_currency = leg_fare.get("currency", currency)
        refundable = "Yes" if room.get("refundable") == 1 else "No"
        paid = leg_fare.get("total_paid", 0)
        total = leg_fare.get("total_price", 0)

        lines += [
            "",
            f"   [{i}] {h.get('name', 'N/A')}",
            f"       Booking ID  : {leg.get('booking_id', 'N/A')}",
            f"       Status      : {leg.get('status', 'N/A')}",
            f"       Address     : {addr.get('address_line_one', '')},"
            f" {addr.get('city_name', '')}",
            f"       Check-in    : {h.get('check_in_datetime', 'N/A')}",
            f"       Check-out   : {h.get('check_out_datetime', 'N/A')}",
            f"       Nights      : {h.get('no_of_nights', 'N/A')}",
            f"       Room        : {room.get('name', 'N/A')}",
            f"       Refundable  : {refundable}",
            f"       Fare        : {leg_currency} {total:.2f}"
            f" (paid: {paid:.2f})",
        ]

        cancel_info = room.get("cancellation_info", [])
        if cancel_info:
            desc = cancel_info[0].get("description", "N/A")
            lines.append(f"       Cancellation: {desc}")

    # ── Cars / Trains / Buses ────────────────────────────────────────────────
    for mode, icon in [("cars", "🚗"), ("trains", "🚆"), ("buses", "🚌")]:
        count = data.get(mode, {}).get("count", 0)
        if count > 0:
            lines += ["", f"{icon} {mode.upper()}: {count} booking(s)"]

    lines += ["", "═" * 50]
    return "\n".join(lines)
