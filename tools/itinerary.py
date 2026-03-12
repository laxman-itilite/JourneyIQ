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
    if trip.get("voucher_link"):
        lines.append(f"   Voucher     : {trip['voucher_link']}")

    # ── Traveller ────────────────────────────────────────────────────────────
    user = data.get("user_details", {})
    lines += [
        "",
        "👤 TRAVELLER",
        f"   Name   : {user.get('full_name', 'N/A')}",
        f"   Email  : {user.get('email', 'N/A')}",
        f"   Phone  : {user.get('contact_no', 'N/A')}",
        f"   Gender : {user.get('sex', 'N/A')}",
        f"   DOB    : {user.get('dob', 'N/A')}",
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
        lines += ["", f"   {'─' * 44}"]
        lines += _format_hotel_leg(i, leg, currency)

    # ── Cars / Trains / Buses ────────────────────────────────────────────────
    for mode, icon in [("cars", "🚗"), ("trains", "🚆"), ("buses", "🚌")]:
        count = data.get(mode, {}).get("count", 0)
        if count > 0:
            lines += ["", f"{icon} {mode.upper()}: {count} booking(s)"]

    lines += ["", "═" * 50]
    return "\n".join(lines)


def _format_hotel_leg(i: int, leg: dict, trip_currency: str) -> list[str]:
    lines: list[str] = []
    h = leg.get("hotel_details", {})
    addr = h.get("address", {})
    loc = h.get("location", {})
    room = leg.get("room_details", [{}])[0]
    leg_fare = leg.get("fare", {})
    c = leg_fare.get("currency", trip_currency)

    # ── Basic Info ───────────────────────────────────────────────────────────
    stars = h.get("star_category", "")
    star_str = f" ({'⭐' * int(float(stars))})" if stars else ""
    lines += [
        f"   [{i}] {h.get('name', 'N/A')}{star_str}",
        f"       Booking ID   : {leg.get('booking_id', 'N/A')}",
        f"       Status       : {leg.get('status', 'N/A')}",
        f"       Vendor       : {leg.get('vendor', 'N/A')}",
    ]

    # ── Address ──────────────────────────────────────────────────────────────
    city = addr.get("city_name", "")
    state = addr.get("state_name") or addr.get("state_code", "")
    country = (
        addr.get("country_name") or addr.get("country_code", "")
    )
    phone = (
        addr.get("contact_no")
        or addr.get("phone_number")
        or "N/A"
    )
    full_addr = ", ".join(
        filter(
            None,
            [addr.get("address_line_one"), city, state, country],
        )
    )
    lines += [
        f"       Address      : {full_addr or 'N/A'}",
        f"       ZIP          : {addr.get('zip_code') or 'N/A'}",
        f"       Phone        : {phone}",
    ]

    # ── Map / Location ───────────────────────────────────────────────────────
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    if lat and lon:
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        lines += [
            f"       Location     : {lat}, {lon}",
            f"       Maps         : {maps_url}",
        ]

    # ── Ratings ──────────────────────────────────────────────────────────────
    if h.get("rating"):
        lines.append(
            f"       Rating       : {h['rating']} ⭐"
            f" ({h.get('reviews', 'N/A')} reviews)"
        )

    # ── Stay Details ─────────────────────────────────────────────────────────
    lines += [
        f"       Check-in     : {h.get('check_in_datetime', 'N/A')}",
        f"       Check-out    : {h.get('check_out_datetime', 'N/A')}",
        f"       Nights       : {h.get('no_of_nights', 'N/A')}",
        f"       Room         : {room.get('name', 'N/A')}",
    ]

    # ── Meals ────────────────────────────────────────────────────────────────
    breakfast = "✅" if room.get("breakfast") else "❌"
    lunch = "✅" if room.get("lunch") else "❌"
    dinner = "✅" if room.get("dinner") else "❌"
    lines.append(
        f"       Meals        : "
        f"Breakfast {breakfast}  Lunch {lunch}  Dinner {dinner}"
    )

    # ── Payment & Loyalty ────────────────────────────────────────────────────
    refundable = "Yes" if room.get("refundable") == 1 else "No"
    loyalty = (
        "✅ Eligible"
        if room.get("earn_loyalty_points")
        else "❌ Not eligible"
    )
    lines += [
        f"       Refundable   : {refundable}",
        f"       Payment Type : {room.get('payment_type', 'N/A')}",
        f"       Payment Mode : {room.get('payment_mode', 'N/A')}",
        f"       Loyalty Pts  : {loyalty}",
    ]

    # ── Membership ───────────────────────────────────────────────────────────
    pax_list = room.get("pax_details", [])
    for pax in pax_list:
        membership = pax.get("membership", {})
        mem_number = membership.get("number")
        mem_name = (
            membership.get("name") or membership.get("first_name")
        )
        if mem_number:
            lines.append(
                f"       Membership   : {mem_name or 'N/A'}"
                f" — #{mem_number}"
            )

    # ── Fare ─────────────────────────────────────────────────────────────────
    total = leg_fare.get("total_price", 0)
    paid = leg_fare.get("total_paid", 0)
    to_pay = leg_fare.get("to_be_paid", 0)
    tax = leg_fare.get("tax", 0)
    base = leg_fare.get("base_price", 0)
    lines += [
        f"       Fare         : {c} {total:.2f}"
        f"  (base: {base:.2f}, tax: {tax:.2f})",
        f"       Paid         : {c} {paid:.2f}"
        f"  |  To Pay: {c} {to_pay:.2f}",
    ]

    # ── Cancellation Policy ──────────────────────────────────────────────────
    cancel_info = room.get("cancellation_info", [])
    if cancel_info:
        ci = cancel_info[0]
        desc = ci.get("description", "N/A")
        lines.append(f"       Cancellation : {desc}")
        if ci.get("date_before"):
            lines.append(
                f"       Cancel Before: {ci['date_before']}"
            )
        charge = ci.get("display_total_charges")
        if charge:
            lines.append(f"       Cancel Charge: {c} {charge}")

    # ── Policy Breach ────────────────────────────────────────────────────────
    policy = leg.get("policy")
    if policy and policy.get("is_breached"):
        amt = policy.get("breached_amount", 0)
        pct = policy.get("breached_percent", 0)
        lines.append(
            f"       ⚠️  Policy    : Breached by"
            f" {c} {amt:.2f} ({pct}%)"
        )

    # ── Voucher ──────────────────────────────────────────────────────────────
    if leg.get("voucher_link"):
        lines.append(
            f"       Voucher      : {leg['voucher_link']}"
        )

    return lines

