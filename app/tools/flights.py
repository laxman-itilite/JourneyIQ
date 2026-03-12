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
    """Build common headers for fast-api-qa (HOTEL_STATIC_BASE_URL) endpoints."""
    token = auth_token or _config.get_user_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "client-id": _client_id_from_trip(trip_id),
        "role": "traveler",
        "content-type": "application/json",
    }


async def _fetch_cancellation_details_raw(trip_id: str) -> dict | None:
    """Internal: call the cancellation-details API and return raw JSON."""
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['flight_cancellation_details']}"
    params = {"trip_id": trip_id}
    headers = _auth_headers(trip_id)
    print(f"[flight-cancel] GET cancellation-details")
    print(f"  url      : {url}")
    print(f"  params   : {params}")
    print(f"  client-id: {headers.get('client-id')}")
    result = await make_get_request(url, params=params, headers=headers)
    if result is None:
        print(f"[flight-cancel] ERROR: cancellation-details returned None for trip={trip_id}")
    else:
        print(f"[flight-cancel] cancellation-details OK")
        print(f"  root_keys           : {list(result.keys())}")
        print(f"  cancellation_detail_id: {result.get('cancellation_detail_id')}")
        print(f"  is_valid_cancellation : {result.get('is_valid_cancellation_call')}")
    return result


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

    # Surface the cancellation_detail_id (needed as context for POST)
    cancel_detail_id = data.get("cancellation_detail_id", "N/A")
    is_valid = data.get("is_valid_cancellation_call", False)
    lines.append(f"  Cancellation Detail ID : {cancel_detail_id}")
    lines.append(f"  Valid for Cancellation : {'Yes' if is_valid else 'No'}")

    if not is_valid:
        lines.append("  ⚠ This trip is not eligible for cancellation at this time.")

    leg_details = data.get("confirmation_result", {}).get("leg_details", [])
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
            lines.append(
                f"  Booking Cost   : {symbol}{total:.2f} {currency} (pax {pax_id})"
            )

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
                lines.append(
                    f"  Cancel Charge  : {symbol}{min_price:.2f} {currency}"
                    f" (pax {pax_id})"
                )
            else:
                lines.append(
                    f"  Cancel Charge  : {symbol}{min_price:.2f}–"
                    f"{symbol}{max_price:.2f} {currency} (pax {pax_id})"
                )
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
            lines.append(
                f"  Passengers     : {', '.join(str(p) for p in remaining)}"
            )

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

    This tool internally fetches cancellation details and passes the raw
    response as the POST body (as required by the API).
    Only call this after the user has reviewed cancellation details and
    explicitly confirmed they want to proceed.

    Args:
        trip_id: The trip ID (e.g. '0600-1241').
        leg_request_ids: List of leg_request_id values to cancel
                         (from get_flight_cancellation_details output).
    """
    # Step 1: Fetch fresh cancellation details
    raw = await _fetch_cancellation_details_raw(trip_id)
    if not raw:
        return f"Unable to fetch cancellation details for trip '{trip_id}'. Cannot proceed."

    # Step 2: Verify the requested leg IDs exist in the response
    all_legs = (
        raw.get("confirmation_result", {}).get("leg_details", [])
        or raw.get("leg_details", [])
    )
    available_ids = [
        leg["leg_request_id"]
        for leg in all_legs
        if leg.get("mode") == "flight" and "leg_request_id" in leg
    ]
    print(f"[flight-cancel] requested_leg_ids : {leg_request_ids}")
    print(f"[flight-cancel] available_leg_ids : {available_ids}")
    missing = [lid for lid in leg_request_ids if lid not in available_ids]
    if missing:
        return (
            f"Leg IDs not found in cancellation details: {missing}. "
            f"Available: {available_ids}"
        )

    # Step 3: Build the POST payload.
    # The API (CancellationRequestPayload) requires these fields at root level:
    #   - trip_id
    #   - cancellation_detail_id
    #   - leg_details  (hoisted from confirmation_result)
    url = f"{HOTEL_STATIC_BASE_URL}{ENDPOINTS['flight_cancellation_request']}"
    conf = raw.get("confirmation_result", {})
    raw_leg_details = conf.get("leg_details", [])

    # The POST endpoint (CancellationRequestPayload) expects each leg to have:
    #   pax_list               ← leg["remaining_pax"] as strings  (e.g. ["1737"])
    #   flight_get_can_details ← the full leg object itself
    # All other leg fields are passed through as-is.
    def _enrich_leg(leg: dict) -> dict:
        enriched = dict(leg)
        if "pax_list" not in enriched:
            enriched["pax_list"] = [str(p) for p in leg.get("remaining_pax", [])]
        else:
            enriched["pax_list"] = [str(p) for p in enriched["pax_list"]]
        if "flight_get_can_details" not in enriched:
            enriched["flight_get_can_details"] = leg
        return enriched

    leg_details = [_enrich_leg(leg) for leg in raw_leg_details]

    # Build display_log — keyed by leg_request_id
    # Mirrors the structure the API expects:
    #   { <leg_request_id>: { mode, cancellation_charge_available,
    #       booking_charge_available, departed, data: { <pax_id>: {...} },
    #       minDeductions, maxDeductions, min_leg_refund_amount, max_leg_refund_amount } }
    def _build_display_log(legs: list[dict]) -> dict:
        log: dict = {}
        for leg in legs:
            leg_req_id = leg.get("leg_request_id")
            if not leg_req_id:
                continue
            pax_ids = leg.get("remaining_pax", [])
            cancel_details_root = (
                leg.get("cancellation_details", {})
                   .get("billed_to_company", {})
                   .get("price_currency_splitup", {})
                   .get("traveller_fare", {})
            )
            price_cat_root = (
                leg.get("price_category", {})
                   .get("billed_to_company", {})
                   .get("price_currency_splitup", {})
                   .get("traveller_fare", {})
            )
            data: dict = {}
            for pax_id in pax_ids:
                pax_str = str(pax_id)
                # Determine pax_type from passenger_type_details (default ADT)
                pax_type = "ADT"
                cancel_price = cancel_details_root.get(pax_str, {})
                booking_price = price_cat_root.get(pax_str, {})
                data[pax_str] = {
                    "pax_type": pax_type,
                    "cancel_price_details": cancel_price,
                    "booking_price_details": booking_price,
                }
            # Refund amounts = booking total - cancellation charges
            min_deductions = 0
            max_deductions = 0
            total_price = 0.0
            for pax_str, pax_data in data.items():
                bp = pax_data.get("booking_price_details", {})
                cp = pax_data.get("cancel_price_details", {})
                total_price += bp.get("total_price", 0) or 0
                min_deductions += cp.get("min_total_price", 0) or 0
                max_deductions += cp.get("max_total_price", 0) or 0
            min_refund = round(total_price - max_deductions, 2)
            max_refund = round(total_price - min_deductions, 2)
            log[leg_req_id] = {
                "mode": leg.get("mode", "flight"),
                "cancellation_charge_available": leg.get("cancellation_charge_available", False),
                "booking_charge_available": leg.get("booking_charge_available", False),
                "departed": leg.get("departed", False),
                "data": data,
                "minDeductions": min_deductions,
                "maxDeductions": max_deductions,
                "min_leg_refund_amount": min_refund,
                "max_leg_refund_amount": max_refund,
            }
        return log

    display_log = _build_display_log(raw_leg_details)

    # Overall min/max refund amounts across all legs
    min_total_refund = round(sum(v["min_leg_refund_amount"] for v in display_log.values()), 2)
    max_total_refund = round(sum(v["max_leg_refund_amount"] for v in display_log.values()), 2)

    payload = {
        "trip_id": trip_id,
        "cancellation_detail_id": raw.get("cancellation_detail_id"),
        "leg_details": leg_details,
        "display_log": display_log,
        "created_by": _config.get_current_user_id(),
        "min_total_refund_amount": min_total_refund,
        "max_total_refund_amount": max_total_refund,
    }
    print("[flight-cancel] POST cancellation-request")
    print(f"  url                    : {url}")
    print(f"  trip_id                : {payload['trip_id']}")
    print(f"  cancellation_detail_id : {payload['cancellation_detail_id']}")
    print(f"  created_by             : {payload['created_by']}")
    print(f"  leg_details count      : {len(leg_details)}")
    print(
        "[flight-cancel] FULL PAYLOAD:\n"
        + json.dumps(payload, indent=2)
    )
    response = await make_post_request(
        url, payload, headers=_auth_headers(trip_id)
    )

    if not response:
        print(f"[flight-cancel] ERROR: POST cancellation-request returned None | trip_id={trip_id}")
        return "Flight cancellation request failed. The API did not return a response."

    print(f"[flight-cancel] POST cancellation-request SUCCESS")
    print(f"  response_keys: {list(response.keys())}")
    print(f"  response     : {json.dumps(response)[:500]}")

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
