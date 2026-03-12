import asyncio
import logging

from config import API_BASE_URL, HOTEL_STATIC_BASE_URL, ENDPOINTS
from services import make_get_request, make_post_request

logger = logging.getLogger(__name__)


async def get_trip_itinerary(trip_id: str, auth_token: str) -> str:
    """Get the full itinerary for a specific trip including hotel,
    flight, fare, traveller details, amenities, descriptions
    and room photos.

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

    # ── Enrich hotel legs with static data (parallel) ─────────────────
    hotel_legs = data.get("hotels", {}).get("legs", [])
    if hotel_legs:
        static_results = await _fetch_all_hotel_static(
            hotel_legs, auth_token
        )
        for leg, static in zip(hotel_legs, static_results):
            leg["_static"] = static  # None if fetch failed

    return _format_itinerary(data)


def register_itinerary_tools(mcp) -> None:
    """Register all itinerary-related tools."""
    mcp.tool()(get_trip_itinerary)


async def _fetch_all_hotel_static(
    legs: list, auth_token: str
) -> list[dict | None]:
    """Fetch static hotel details for all legs concurrently."""
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['hotel_room_details']}"
    headers = {
        "authorization": f"Bearer {auth_token}",
        "content-type": "application/json",
    }

    async def _fetch_one(leg: dict) -> dict | None:
        room_details = leg.get("room_details", [])
        room_id = room_details[0].get("id", "") if room_details else ""
        payload = {
            "mode": "hotel",
            "leg_details": {
                "leg_info_id": leg.get("leg_request_id", ""),
                "hotel_unique_id": leg.get("id", ""),
                "room_id": room_id,
                "is_booked": True,
            },
        }
        try:
            result = await make_post_request(
                url, payload, headers=headers
            )
            if result and result.get("status_code") == 200:
                return result.get("response_data")
        except Exception as e:
            logger.warning("Hotel static fetch failed: %s", e)
        return None

    return list(
        await asyncio.gather(*[_fetch_one(leg) for leg in legs])
    )


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
        for i, leg in enumerate(flights.get("legs", []), 1):
            lines += ["", f"   {'─' * 44}"]
            lines += _format_flight_leg(i, leg)
    else:
        lines += ["", "✈️  FLIGHTS: None"]

    # ── Hotels ───────────────────────────────────────────────────────────────
    hotels = data.get("hotels", {})
    hotel_legs = hotels.get("legs", [])
    lines += ["", f"🏨 HOTELS ({hotels.get('count', 0)})"]

    for i, leg in enumerate(hotel_legs, 1):
        lines += ["", f"   {'─' * 44}"]
        lines += _format_hotel_leg(i, leg, currency)

    # ── Cars ─────────────────────────────────────────────────────────────────
    cars = data.get("cars", {})
    car_legs = cars.get("legs", [])
    if cars.get("count", 0) > 0:
        lines += ["", f"� CARS ({cars['count']})"]
        for i, leg in enumerate(car_legs, 1):
            lines += ["", f"   {'─' * 44}"]
            lines += _format_car_leg(i, leg)

    # ── Trains ───────────────────────────────────────────────────────────────
    trains = data.get("trains", {})
    if trains.get("count", 0) > 0:
        lines += ["", f"🚆 TRAINS: {trains['count']} booking(s)"]

    # ── Buses ────────────────────────────────────────────────────────────────
    buses = data.get("buses", {})
    if buses.get("count", 0) > 0:
        lines += ["", f"🚌 BUSES: {buses['count']} booking(s)"]

    # ── Charge Summary ───────────────────────────────────────────────────────
    charge = data.get("charge_summary", {})
    breakups = charge.get("breakups", [])
    if breakups:
        ch_cur = charge.get("currency", "")
        ch_total = charge.get("total", 0)
        lines += [
            "",
            f"🧾 CHARGE SUMMARY"
            f" (Total: {ch_cur} {ch_total:.2f})",
        ]
        for b in breakups:
            title_b = b.get("title", "N/A")
            total_b = b.get("total", 0) or 0
            pmode = b.get("payment_mode") or "—"
            pdate = b.get("payment_date") or "—"
            lines += [
                f"   • {title_b}",
                f"     Amount  : {ch_cur} {total_b:.2f}"
                f"  (base: {b.get('base_amount') or 0:.2f})",
                f"     Payment : {pmode}  [{pdate}]",
            ]
            if b.get("confirmation_code"):
                lines.append(
                    f"     Conf #  : {b['confirmation_code']}"
                )

    lines += ["", "═" * 50]
    return "\n".join(lines)


def _format_flight_leg(i: int, leg: dict) -> list[str]:
    lines: list[str] = []
    frm = leg.get("from", {})
    to = leg.get("to", {})
    airline = leg.get("airline", {})
    fare = leg.get("fare", {})
    c = fare.get("currency", "")

    # ── Basic Info ───────────────────────────────────────────────────────────
    airline_str = (
        f"{airline.get('name', 'N/A')}"
        f" {airline.get('code', '')}{airline.get('number', '')}"
    )
    lines += [
        f"   [{i}] {frm.get('iata', '?')} → {to.get('iata', '?')}"
        f"  |  {airline_str}",
        f"       Status       : {leg.get('status', 'N/A')}",
        f"       PNR          : {leg.get('pnr', 'N/A')}",
        f"       Booking ID   : {leg.get('booking_id', 'N/A')}",
        f"       Trip Type    : {leg.get('trip_type', 'N/A')}",
        f"       Travel Type  : {leg.get('travel_type', 'N/A')}",
        f"       Vendor       : {leg.get('vendor', 'N/A')}",
    ]

    # ── Route ────────────────────────────────────────────────────────────────
    lines += [
        f"       Departure    : {frm.get('city', 'N/A')}"
        f" ({frm.get('airport_name', '')},"
        f" T{frm.get('terminal', '?')})"
        f" @ {frm.get('departure_datetime', 'N/A')}",
        f"       Arrival      : {to.get('city', 'N/A')}"
        f" ({to.get('airport_name', '')},"
        f" T{to.get('terminal', '?')})"
        f" @ {to.get('arrival_datetime', 'N/A')}",
        f"       Stops        : {leg.get('no_of_stops', 0)}",
    ]

    # ── Segments ─────────────────────────────────────────────────────────────
    segments = leg.get("segments", [])
    for seg in segments:
        seg_airline = seg.get("airline", {})
        seg_from = seg.get("from", {})
        seg_to = seg.get("to", {})
        baggage = seg.get("baggage", {})
        lines += [
            f"       Segment      :"
            f" {seg_from.get('iata', '?')}"
            f" → {seg_to.get('iata', '?')}"
            f"  ({seg.get('duration', 'N/A')})",
            f"         Cabin      : {seg.get('cabin_class', 'N/A')}",
            f"         Fare Brand : {seg.get('brand_fare', 'N/A')}",
            f"         Operator   :"
            f" {seg_airline.get('operator', 'N/A')}",
            f"         Cabin Bag  : {baggage.get('cabin', 'N/A')}",
            f"         Check-in   : {baggage.get('checkin', 'N/A')}",
        ]
        # Per-pax ticket numbers
        for pax in seg.get("pax_details", []):
            ticket = pax.get("ticket_number")
            pax_status = pax.get("status", "N/A")
            if ticket:
                lines.append(
                    f"         Ticket #   : {ticket}"
                    f"  ({pax_status})"
                )

    # ── Fare ─────────────────────────────────────────────────────────────────
    total = fare.get("total_price", 0) or 0
    base = fare.get("base_price", 0) or 0
    tax = fare.get("tax", 0) or 0
    lines.append(
        f"       Fare         : {c} {total:.2f}"
        f"  (base: {base:.2f}, tax: {tax:.2f})"
    )

    # ── Refundable & Policy ──────────────────────────────────────────────────
    refundable = "Yes" if leg.get("refundable") == 1 else "No"
    lines.append(f"       Refundable   : {refundable}")

    policy = leg.get("policy", {})
    if policy and policy.get("is_breached"):
        amt = policy.get("breached_amount", 0)
        pct = policy.get("breached_percent", 0)
        lines.append(
            f"       ⚠️  Policy    : Breached by"
            f" {c} {amt:.2f} ({pct}%)"
        )

    # ── Cancellation ─────────────────────────────────────────────────────────
    cancel = leg.get("cancellation_info", {})
    if isinstance(cancel, dict) and cancel:
        times = list(cancel.get("time", {}).items())
        if times:
            dl, charge = times[0]
            lines.append(
                f"       Cancel By    : {dl}"
                f"  (charge: {cancel.get('currency', c)}"
                f" {charge:.2f})"
            )

    # ── Voucher ──────────────────────────────────────────────────────────────
    if leg.get("voucher_link"):
        lines.append(f"       Voucher      : {leg['voucher_link']}")

    return lines


def _format_car_leg(i: int, leg: dict) -> list[str]:
    lines: list[str] = []
    car = leg.get("car_details", {})
    pickup = leg.get("pickup", {})
    dropoff = leg.get("dropoff", {})
    fare = leg.get("fare", {})
    c = fare.get("currency", "USD")

    # ── Basic Info ───────────────────────────────────────────────────────────
    lines += [
        f"   [{i}] {car.get('vendor_name', 'N/A')}"
        f"  — {car.get('model_name', 'N/A')}",
        f"       Status       : {leg.get('status', 'N/A')}",
        f"       PNR          : {leg.get('pnr', 'N/A')}",
        f"       CSR PNR      : {leg.get('csr_pnr', 'N/A')}",
        f"       Trip Type    : {leg.get('trip_type', 'N/A')}",
        f"       Subtype      :"
        f" {leg.get('subtype_display_name', 'N/A')}",
    ]

    # ── Vehicle Details ──────────────────────────────────────────────────────
    ac = "Yes" if car.get("air_condition") else "No"
    lines += [
        f"       Class        : {car.get('class', 'N/A')}",
        f"       Vehicle Type : {car.get('vehicle_type', 'N/A')}",
        f"       Doors        : {car.get('door_count', 'N/A')}",
        f"       Passengers   : {car.get('paxct', 'N/A')}",
        f"       Luggage      : {car.get('baggage_count', 'N/A')} bag(s)",
        f"       A/C          : {ac}",
        f"       Rate Type    : {car.get('rate_type_text', 'N/A')}",
        f"       Rate/Period  :"
        f" {c} {car.get('rate_for_period', 0):.2f}"
        f" ({car.get('rate_period', 'N/A')})",
        f"       Total Days   : {car.get('total_days', 'N/A')}",
    ]
    if car.get("discount_number"):
        lines.append(
            f"       Discount #   : {car['discount_number']}"
        )

    # ── Pickup & Dropoff ─────────────────────────────────────────────────────
    lines += [
        f"       Pick-up      : {pickup.get('location', 'N/A')}"
        f" ({pickup.get('type', '')})"
        f" @ {pickup.get('datetime', 'N/A')}",
        f"       Drop-off     : {dropoff.get('location', 'N/A')}"
        f" ({dropoff.get('type', '')})"
        f" @ {dropoff.get('datetime', 'N/A')}",
    ]

    # ── Location / Map ───────────────────────────────────────────────────────
    lat = car.get("latitude")
    lon = car.get("longitude")
    if lat and lon:
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        lines += [
            f"       Location     : {lat}, {lon}",
            f"       Maps         : {maps_url}",
        ]

    # ── Fare ─────────────────────────────────────────────────────────────────
    total = fare.get("total_price", 0) or 0
    base = fare.get("base_price", 0) or 0
    tax = fare.get("tax", 0) or 0
    lines.append(
        f"       Fare         : {c} {total:.2f}"
        f"  (base: {base:.2f}, tax: {tax:.2f})"
    )

    # ── Policy ───────────────────────────────────────────────────────────────
    if car.get("out_of_policy"):
        reason = car.get("out_of_policy_reason") or "N/A"
        lines.append(f"       ⚠️  Policy    : Out of policy — {reason}")

    # ── Key Instructions ─────────────────────────────────────────────────────
    instructions = car.get("instructions", [])
    if instructions:
        lines.append("       Instructions :")
        for ins in instructions:
            name = ins.get("name", "")
            lines.append(f"         • {name}")

    # ── Voucher ──────────────────────────────────────────────────────────────
    if leg.get("voucher_link"):
        lines.append(
            f"       Voucher      : {leg['voucher_link']}"
        )

    return lines


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

    # ── Inclusions ───────────────────────────────────────────────────────────
    # Property-level inclusions (plain strings)
    prop_inc = h.get("inclusions", [])
    if prop_inc and isinstance(prop_inc[0], str):
        lines.append(
            f"       Property Inc : {', '.join(prop_inc)}"
        )
    # Room-level inclusions (list of {id, name} objects)
    room_inc = room.get("inclusions", [])
    if room_inc:
        inc_names = [
            x.get("name", "")
            for x in room_inc
            if isinstance(x, dict) and x.get("name")
        ]
        if inc_names:
            # Show as a wrapped comma-separated list
            lines.append(
                f"       Room Inc     : {', '.join(inc_names)}"
            )

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

    # ── Static Enrichment (amenities, description, photos) ───────────────────
    static = leg.get("_static")
    if static:
        # Property description — word-wrapped at ~65 chars
        desc = static.get("property_description", "").strip()
        if desc:
            lines.append("       Description  :")
            words, buf = desc.split(), []
            for word in words:
                if sum(len(w) + 1 for w in buf) + len(word) > 65:
                    lines.append("         " + " ".join(buf))
                    buf = [word]
                else:
                    buf.append(word)
            if buf:
                lines.append("         " + " ".join(buf))

        # Check-in / check-out times (from static, more precise)
        ci_time = static.get("check_in", "")
        co_time = static.get("check_out", "")
        if ci_time or co_time:
            lines.append(
                f"       Check-in Time: {ci_time or 'N/A'}"
                f"  |  Check-out: {co_time or 'N/A'}"
            )

        # Property-level amenities
        prop_amenities = [
            a.get("amenity_name", "")
            for a in static.get("amenities", [])
            if a.get("amenity_name")
        ]
        if prop_amenities:
            lines.append(
                f"       Prop Amenities: {', '.join(prop_amenities)}"
            )

        # Room static details
        static_rooms = static.get("room_details", [])
        if static_rooms:
            sr = static_rooms[0]

            # Bedding
            bedding = [
                b.get("description", "")
                for b in sr.get("bedding", [])
                if b.get("description")
            ]
            if bedding:
                lines.append(
                    f"       Bedding      : {', '.join(bedding)}"
                )

            # Room amenities
            room_amenities = [
                a.get("name", "")
                for a in sr.get("amenities", [])
                if a.get("name")
            ]
            if room_amenities:
                lines.append(
                    f"       Room Amenities: "
                    f"{', '.join(room_amenities)}"
                )

            # Room feature quick-glance
            feats = [
                f"A/C {'✅' if sr.get('is_ac') else '❌'}",
                f"WiFi {'✅' if sr.get('is_wifi') else '❌'}",
                f"TV {'✅' if sr.get('is_tv') else '❌'}",
                f"Coffee {'✅' if sr.get('is_coffee') else '❌'}",
                f"Parking"
                f" {'✅' if sr.get('parking_available') else '❌'}",
            ]
            if sr.get("airport_transfer_available"):
                feats.append("Airport Transfer ✅")
            lines.append(
                f"       Room Features: {' | '.join(feats)}"
            )

            sq_ft = sr.get("square_footage", 0)
            if sq_ft:
                lines.append(
                    f"       Size         : {sq_ft} sq ft"
                )

            # Photos — first 3 only
            photos = sr.get("photos", [])
            if photos:
                shown = min(len(photos), 3)
                lines.append(
                    f"       Photos"
                    f" ({shown}/{len(photos)}):"
                )
                for p in photos[:3]:
                    lines.append(f"         {p}")

    # ── Voucher ──────────────────────────────────────────────────────────────
    if leg.get("voucher_link"):
        lines.append(
            f"       Voucher      : {leg['voucher_link']}"
        )

    return lines

