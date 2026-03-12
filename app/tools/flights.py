"""Flight cancellation tools for the Itilite Travel Assistant."""

import json
import logging

from app.config import HOTEL_STATIC_BASE_URL, ENDPOINTS
import app.config as _config
from app.services import make_get_request, make_post_request

logger = logging.getLogger(__name__)


def _client_id_from_trip(trip_id: str) -> str:
    """Extract client ID from trip ID. e.g. '0600-1241' → '600'."""
    prefix = trip_id.split("-")[0]
    return str(int(prefix))  # strips leading zeros


def _auth_headers(trip_id: str, auth_token: str = "") -> dict:
    """Build common headers for trip-modify endpoints."""
    token = auth_token or _config.get_user_access_token()
    return {
        "authorization": f"Bearer {token}",
        "client-id": _client_id_from_trip(trip_id),
        "role": "traveler",
        "content-type": "application/json",
    }


async def _fetch_cancellation_details_raw(trip_id: str) -> dict | None:
    """Internal: call the cancellation-details API and return raw JSON."""
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['flight_cancellation_details']}"
    params = {"trip_id": trip_id}
    return await make_get_request(url, params=params, headers=_auth_headers(trip_id))


# ── Tool 1: Get cancellation details ─────────────────────────────────────────


async def get_flight_cancellation_details(trip_id: str) -> str:
    """Get cancellation eligibility, refund estimates, and eligible legs
    for a trip's flight bookings.

    Args:
        trip_id: The trip ID (e.g. '0600-1241').
    """
    raw = await _fetch_cancellation_details_raw(trip_id)
    if not raw:
        return f"Unable to fetch cancellation details for trip '{trip_id}'."

    return _format_cancellation_details(raw, trip_id)


def _format_cancellation_details(data: dict, trip_id: str) -> str:
    """Format the cancellation-details response into a human-readable summary."""
    lines: list[str] = []
    lines.append(f"Flight Cancellation Details — Trip {trip_id}")
    lines.append("=" * 50)

    leg_details = data.get("leg_details", [])
    if not leg_details:
        lines.append("No cancellable flight legs found for this trip.")
        return "\n".join(lines)

    for leg in leg_details:
        mode = leg.get("mode", "unknown")
        if mode != "flight":
            continue

        leg_req_id = leg.get("leg_request_id", "N/A")
        from_city = leg.get("travel_from_city", "N/A")
        to_city = leg.get("travel_to_city", "N/A")
        dep_date = leg.get("departure_date", "N/A")
        dep_time = leg.get("departure_time", "N/A")
        arr_date = leg.get("arrival_date", "N/A")
        arr_time = leg.get("arrival_time", "N/A")
        pnr = leg.get("pnr", "N/A")
        booking_track_id = leg.get("booking_track_id", "N/A")
        departed = leg.get("departed", False)
        can_cancel = leg.get("cancellation_charge_available", False)

        lines.append("")
        lines.append(f"  Flight: {from_city} → {to_city}")
        lines.append(f"  Leg Request ID : {leg_req_id}")
        lines.append(f"  PNR            : {pnr}")
        lines.append(f"  Booking Track  : {booking_track_id}")
        lines.append(f"  Departure      : {dep_date} {dep_time}")
        lines.append(f"  Arrival        : {arr_date} {arr_time}")
        lines.append(f"  Departed       : {'Yes' if departed else 'No'}")
        lines.append(f"  Cancellable    : {'Yes' if can_cancel else 'No'}")

        # Price & refund info
        price_cat = leg.get("price_category", {})
        billed = price_cat.get("billed_to_company", {})
        splitup = billed.get("price_currency_splitup", {})
        traveller_fare = splitup.get("traveller_fare", {})
        for pax_id, fare in traveller_fare.items():
            currency = fare.get("currency", "")
            symbol = fare.get("currency_symbol", "")
            total = fare.get("total_price", 0)
            lines.append(f"  Booking Cost   : {symbol}{total:.2f} {currency} (pax {pax_id})")

        cancel_details = leg.get("cancellation_details", {})
        cancel_billed = cancel_details.get("billed_to_company", {})
        cancel_splitup = cancel_billed.get("price_currency_splitup", {})
        cancel_trav = cancel_splitup.get("traveller_fare", {})
        for pax_id, info in cancel_trav.items():
            currency = info.get("currency", "")
            symbol = info.get("currency_symbol", "")
            min_price = info.get("min_total_price", 0)
            max_price = info.get("max_total_price", 0)
            non_refundable = info.get("non_refundable_tc", False)
            if min_price == max_price:
                lines.append(f"  Cancel Charge  : {symbol}{min_price:.2f} {currency} (pax {pax_id})")
            else:
                lines.append(f"  Cancel Charge  : {symbol}{min_price:.2f}–{symbol}{max_price:.2f} {currency} (pax {pax_id})")
            lines.append(f"  Non-Refundable : {'Yes' if non_refundable else 'No'}")

        # Refund summary
        per_adult = leg.get("per_adult_charge", {})
        if per_adult:
            min_ch = per_adult.get("min_total_price", 0)
            max_ch = per_adult.get("max_total_price", 0)
            lines.append(f"  Per Adult Charge: {min_ch:.2f}–{max_ch:.2f}")

        # Passengers
        remaining = leg.get("remaining_pax", [])
        if remaining:
            lines.append(f"  Passengers     : {', '.join(str(p) for p in remaining)}")

    # Overall refund
    min_refund = data.get("min_total_refund_amount", 0)
    max_refund = data.get("max_total_refund_amount", 0)
    lines.append("")
    lines.append(f"Total Estimated Refund: {min_refund:.2f}–{max_refund:.2f}")
    lines.append("=" * 50)

    return "\n".join(lines)


# ── Tool 2: Submit cancellation request ──────────────────────────────────────


async def submit_flight_cancellation(trip_id: str, leg_request_ids: list[str]) -> str:
    """Submit a flight cancellation request for specified legs of a trip.

    This tool internally fetches cancellation details to build the request.
    Only call this after the user has reviewed cancellation details and
    explicitly confirmed they want to proceed.

    Args:
        trip_id: The trip ID (e.g. '0600-1241').
        leg_request_ids: List of leg_request_id values to cancel
                         (from get_flight_cancellation_details output).
    """
    # Step 1: Fetch fresh cancellation details to build the POST body
    raw = await _fetch_cancellation_details_raw(trip_id)
    if not raw:
        return f"Unable to fetch cancellation details for trip '{trip_id}'. Cannot proceed."

    cancellation_detail_id = raw.get("_id") or raw.get("cancellation_detail_id")
    if not cancellation_detail_id:
        # Try to find it in the response — some APIs nest it differently
        for key in ("id", "detail_id"):
            if raw.get(key):
                cancellation_detail_id = raw[key]
                break

    if not cancellation_detail_id:
        return "Could not find cancellation_detail_id in the response. Cannot proceed."

    # Step 2: Build leg_details array from the matching legs
    all_legs = raw.get("leg_details", [])
    target_ids = set(leg_request_ids)
    matched_legs = []

    for leg in all_legs:
        if leg.get("leg_request_id") in target_ids and leg.get("mode") == "flight":
            flight_details = leg.get("flight_get_can_details")
            if not flight_details:
                # Build from basic_details in the nested structure
                basic = leg.get("basic_details")
                if basic:
                    flight_details = {"basic_details": basic}

            matched_legs.append({
                "mode": "flight",
                "leg_request_id": leg["leg_request_id"],
                "pax_list": [str(p) for p in leg.get("remaining_pax", [])],
                "flight_get_can_details": flight_details,
            })

    if not matched_legs:
        available = [
            l["leg_request_id"]
            for l in all_legs
            if l.get("mode") == "flight"
        ]
        return (
            f"No matching flight legs found for IDs: {leg_request_ids}. "
            f"Available flight leg IDs: {available}"
        )

    # Step 3: POST the cancellation request
    payload = {
        "cancellation_detail_id": cancellation_detail_id,
        "trip_id": trip_id,
        "leg_details": matched_legs,
    }

    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['flight_cancellation_request']}"
    response = await make_post_request(url, payload, headers=_auth_headers(trip_id))

    if not response:
        return "Flight cancellation request failed. The API did not return a response."

    # Extract cancellation request ID from response
    req_id = (
        response.get("cancellation_request_id")
        or response.get("request_id")
        or response.get("_id")
    )

    if req_id:
        return (
            f"Flight cancellation request submitted successfully.\n"
            f"Cancellation Request ID: {req_id}\n"
            f"Trip ID: {trip_id}\n"
            f"Legs cancelled: {leg_request_ids}\n"
            f"Use get_flight_cancellation_status to check the progress."
        )

    # Return full response if we can't find a known ID field
    return f"Cancellation request submitted. Response:\n{json.dumps(response, indent=2)}"


# ── Tool 3: Check cancellation status ────────────────────────────────────────


async def get_flight_cancellation_status(
    cancellation_request_id: str, trip_id: str
) -> str:
    """Check the status of a previously submitted flight cancellation request.

    Args:
        cancellation_request_id: The ID returned by submit_flight_cancellation.
        trip_id: The trip ID (e.g. '0600-1241').
    """
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['flight_cancellation_request']}"
    params = {
        "cancellation_request_id": cancellation_request_id,
        "trip_id": trip_id,
    }
    response = await make_get_request(url, params=params, headers=_auth_headers(trip_id))

    if not response:
        return (
            f"Unable to fetch cancellation status for request "
            f"'{cancellation_request_id}' (trip '{trip_id}')."
        )

    return _format_cancellation_status(response, cancellation_request_id)


def _format_cancellation_status(data: dict, request_id: str) -> str:
    """Format the cancellation status response."""
    lines: list[str] = []
    lines.append(f"Cancellation Status — Request {request_id}")
    lines.append("=" * 50)

    status = data.get("status") or data.get("cancellation_status") or "Unknown"
    lines.append(f"  Status: {status}")

    # Try to extract any relevant fields the API might return
    for key in ("refund_amount", "refund_status", "updated_at", "created_at", "message"):
        val = data.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {val}")

    # If there are leg-level statuses
    leg_statuses = data.get("leg_statuses") or data.get("legs") or []
    for leg in leg_statuses:
        leg_id = leg.get("leg_request_id", "N/A")
        leg_status = leg.get("status", "N/A")
        lines.append(f"  Leg {leg_id}: {leg_status}")

    lines.append("=" * 50)
    return "\n".join(lines)
