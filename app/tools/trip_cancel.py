"""Whole-trip cancellation — cancels all active legs in a trip
(flights, hotels, and rental cars) in a single call.
"""

import asyncio
import json
import logging

import app.config as _config
from app.config import (
    HOTEL_STATIC_BASE_URL,
    HOTEL_SERVICE_BASE_URL,
    CAR_SERVICE_BASE_URL,
    API_BASE_URL,
    ENDPOINTS,
)
from app.services import make_get_request, make_post_request

logger = logging.getLogger(__name__)


# ── Helpers shared with individual tools ─────────────────────────────────────

def _client_id_from_trip(trip_id: str) -> str:
    """Extract numeric client ID from trip prefix. '0653-0070' → '653'."""
    try:
        return str(int(trip_id.split("-")[0]))
    except (ValueError, IndexError):
        return ""


def _flight_auth_headers(trip_id: str) -> dict:
    token = _config.get_user_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "client-id": _client_id_from_trip(trip_id),
        "role": "traveler",
        "content-type": "application/json",
    }


# ── Per-mode cancellation helpers ─────────────────────────────────────────────

async def _cancel_hotel(leg_request_id: str) -> dict:
    """Cancel one hotel leg. Returns {leg_request_id, mode, status, detail}."""
    auth_token = _config.get_user_access_token()
    url = f"{HOTEL_SERVICE_BASE_URL}{ENDPOINTS['hotel_cancel']}"
    headers = {"authorization": f"Bearer {auth_token}"}
    payload = {"legRequestIds": [leg_request_id]}

    data = await make_post_request(url, payload, headers=headers)

    if not data:
        return {
            "leg_request_id": leg_request_id,
            "mode": "hotel",
            "status": "failed",
            "detail": "No response from hotel cancellation API.",
        }
    if data.get("success"):
        inner = data.get("data", {})
        return {
            "leg_request_id": leg_request_id,
            "mode": "hotel",
            "status": "cancelled",
            "detail": inner.get("message", "Cancelled successfully."),
        }
    inner = data.get("data", {})
    fail = inner.get("failureResults", [])
    reason = (
        fail[0].get("message", "") if fail
        else data.get("message", "Unknown error")
    )
    return {
        "leg_request_id": leg_request_id,
        "mode": "hotel",
        "status": "failed",
        "detail": reason,
    }


async def _cancel_car(service_master_id: int, cab_id: int) -> dict:
    """Cancel one car leg. Returns {cab_id, mode, status, detail}."""
    auth_token = _config.get_user_access_token()
    url = f"{CAR_SERVICE_BASE_URL}{ENDPOINTS['car_cancel']}"
    headers = {"authorization": f"Bearer {auth_token}"}
    payload = {
        "service_master_id": service_master_id,
        "cab_cancellation_list": [{"cab_id": cab_id}],
    }

    data = await make_post_request(url, payload, headers=headers)

    if not data:
        return {
            "cab_id": cab_id,
            "mode": "car",
            "status": "failed",
            "detail": "No response from car cancellation API.",
        }
    if data.get("status_code") == 200:
        return {
            "cab_id": cab_id,
            "mode": "car",
            "status": "cancelled",
            "detail": data.get("message", "Cancelled successfully."),
        }
    return {
        "cab_id": cab_id,
        "mode": "car",
        "status": "failed",
        "detail": data.get("message", "Unknown error"),
    }


async def _cancel_flights(trip_id: str) -> dict:
    """Cancel all flight legs for a trip via the flight cancellation API.

    Returns {trip_id, mode, status, cancellation_request_id, detail}.
    """
    # Step 1: Fetch cancellation details
    url_details = (
        f"{HOTEL_STATIC_BASE_URL}"
        f"{ENDPOINTS['flight_cancellation_details']}"
    )
    raw = await make_get_request(
        url_details,
        params={"trip_id": trip_id},
        headers=_flight_auth_headers(trip_id),
    )
    if not raw:
        return {
            "trip_id": trip_id,
            "mode": "flight",
            "status": "failed",
            "detail": "Unable to fetch flight cancellation details.",
        }
    if not raw.get("is_valid_cancellation_call", False):
        return {
            "trip_id": trip_id,
            "mode": "flight",
            "status": "skipped",
            "detail": (
                "Flight not eligible for cancellation at this time "
                "(is_valid_cancellation_call=false)."
            ),
        }

    conf = raw.get("confirmation_result", {})
    raw_legs = conf.get("leg_details", [])

    # Step 2: Build the POST payload (same logic as submit_flight_cancellation)
    def _enrich_leg(leg: dict) -> dict:
        enriched = dict(leg)
        if "pax_list" not in enriched:
            enriched["pax_list"] = [
                str(p) for p in leg.get("remaining_pax", [])
            ]
        else:
            enriched["pax_list"] = [str(p) for p in enriched["pax_list"]]
        if "flight_get_can_details" not in enriched:
            enriched["flight_get_can_details"] = leg
        return enriched

    leg_details = [_enrich_leg(leg) for leg in raw_legs]

    def _build_display_log(legs: list[dict]) -> dict:
        log: dict = {}
        for leg in legs:
            leg_req_id = leg.get("leg_request_id")
            if not leg_req_id:
                continue
            pax_ids = leg.get("remaining_pax", [])
            cancel_root = (
                leg.get("cancellation_details", {})
                   .get("billed_to_company", {})
                   .get("price_currency_splitup", {})
                   .get("traveller_fare", {})
            )
            price_root = (
                leg.get("price_category", {})
                   .get("billed_to_company", {})
                   .get("price_currency_splitup", {})
                   .get("traveller_fare", {})
            )
            data: dict = {}
            for pax_id in pax_ids:
                pax_str = str(pax_id)
                data[pax_str] = {
                    "pax_type": "ADT",
                    "cancel_price_details": cancel_root.get(pax_str, {}),
                    "booking_price_details": price_root.get(pax_str, {}),
                }
            min_ded = max_ded = total = 0.0
            for pd in data.values():
                bp = pd.get("booking_price_details", {})
                cp = pd.get("cancel_price_details", {})
                total += bp.get("total_price", 0) or 0
                min_ded += cp.get("min_total_price", 0) or 0
                max_ded += cp.get("max_total_price", 0) or 0
            log[leg_req_id] = {
                "mode": leg.get("mode", "flight"),
                "cancellation_charge_available": leg.get(
                    "cancellation_charge_available", False
                ),
                "booking_charge_available": leg.get(
                    "booking_charge_available", False
                ),
                "departed": leg.get("departed", False),
                "data": data,
                "minDeductions": min_ded,
                "maxDeductions": max_ded,
                "min_leg_refund_amount": round(total - max_ded, 2),
                "max_leg_refund_amount": round(total - min_ded, 2),
            }
        return log

    display_log = _build_display_log(raw_legs)
    min_total = round(
        sum(v["min_leg_refund_amount"] for v in display_log.values()), 2
    )
    max_total = round(
        sum(v["max_leg_refund_amount"] for v in display_log.values()), 2
    )

    payload = {
        "trip_id": trip_id,
        "cancellation_detail_id": raw.get("cancellation_detail_id"),
        "leg_details": leg_details,
        "display_log": display_log,
        "created_by": _config.get_current_user_id(),
        "min_total_refund_amount": min_total,
        "max_total_refund_amount": max_total,
    }

    # Step 3: Submit the cancellation request
    url_request = (
        f"{HOTEL_STATIC_BASE_URL}"
        f"{ENDPOINTS['flight_cancellation_request']}"
    )
    response = await make_post_request(
        url_request, payload, headers=_flight_auth_headers(trip_id)
    )

    if not response:
        return {
            "trip_id": trip_id,
            "mode": "flight",
            "status": "failed",
            "detail": "Flight cancellation request returned no response.",
        }

    req_id = (
        response.get("cancellation_request_id")
        or response.get("request_id")
        or response.get("_id")
    )
    return {
        "trip_id": trip_id,
        "mode": "flight",
        "status": "submitted",
        "cancellation_request_id": req_id,
        "detail": (
            f"Cancellation request submitted "
            f"(ID: {req_id}). Processing asynchronously."
            if req_id
            else json.dumps(response)[:200]
        ),
    }


# ── Public tool ───────────────────────────────────────────────────────────────

async def cancel_entire_trip(trip_id: str) -> str:
    """Cancel all active legs of a trip — flights, hotels, and rental cars —
    in a single call.

    This tool:
    1. Fetches the trip itinerary to discover all legs.
    2. Cancels each leg concurrently (hotels and cars fire in parallel;
       the flight cancellation workflow runs alongside them).
    3. Returns a per-leg summary of what was cancelled, skipped, or failed.

    Only call this AFTER the user has explicitly confirmed they want to
    cancel the entire trip.

    Args:
        trip_id: The trip ID (e.g. '0653-0070').
    """
    # ── 1. Fetch the itinerary to discover all legs ───────────────────────
    auth_token = _config.get_user_access_token()
    itinerary_url = (
        f"{API_BASE_URL}"
        f"{ENDPOINTS['itinerary'].format(trip_id=trip_id)}"
    )
    itinerary = await make_get_request(
        itinerary_url,
        headers={"authorization": f"Bearer {auth_token}"},
    )

    if not itinerary or itinerary.get("status_code") != 200:
        return (
            f"Unable to fetch itinerary for trip '{trip_id}'. "
            "Cannot proceed with cancellation."
        )

    data = itinerary.get("data", {})
    print(
        f"[trip-cancel] itinerary fetched for {trip_id}, "
        f"top-level keys: {list(data.keys())}"
    )

    # ── 2. Collect cancellation tasks ────────────────────────────────────
    tasks: list = []

    # Hotels
    hotel_legs = data.get("hotels", {}).get("legs", [])
    for leg in hotel_legs:
        leg_req_id = leg.get("leg_request_id", "")
        status = (leg.get("status") or "").lower()
        if leg_req_id and status not in ("cancelled", "cancel"):
            tasks.append(_cancel_hotel(leg_req_id))
            print(f"[trip-cancel]   queued hotel  leg_request_id={leg_req_id}")

    # Cars
    car_legs = data.get("cars", {}).get("legs", [])
    for leg in car_legs:
        svc_id = leg.get("service_master_id")
        cab_id = leg.get("car_id")
        status = (leg.get("status") or "").lower()
        if svc_id and cab_id and status not in ("cancelled", "cancel"):
            tasks.append(_cancel_car(int(svc_id), int(cab_id)))
            print(
                f"[trip-cancel]   queued car    "
                f"service_master_id={svc_id} cab_id={cab_id}"
            )

    # Flights — one call handles all legs for the trip
    flight_legs = data.get("flights", {}).get("legs", [])
    has_active_flights = any(
        (leg.get("status") or "").lower() not in ("cancelled", "cancel")
        for leg in flight_legs
    )
    if has_active_flights:
        tasks.append(_cancel_flights(trip_id))
        print(f"[trip-cancel]   queued flights trip_id={trip_id}")

    if not tasks:
        return (
            f"No active legs found to cancel on trip '{trip_id}'. "
            "It may already be fully cancelled."
        )

    # ── 3. Run all cancellations concurrently ────────────────────────────
    results: list[dict] = list(await asyncio.gather(*tasks))
    print(f"[trip-cancel] results: {json.dumps(results, indent=2)}")

    # ── 4. Format the summary ────────────────────────────────────────────
    return _format_trip_cancel_summary(trip_id, results)


def _format_trip_cancel_summary(
    trip_id: str, results: list[dict]
) -> str:
    """Format the per-leg cancellation outcome into a human-readable report."""
    lines: list[str] = [
        f"Trip Cancellation Summary — {trip_id}",
        "=" * 50,
    ]

    icon_map = {
        "cancelled": "✅",
        "submitted": "🕐",
        "skipped": "⏭",
        "failed": "❌",
    }

    for r in results:
        mode = r.get("mode", "unknown").upper()
        status = r.get("status", "unknown")
        icon = icon_map.get(status, "❓")
        detail = r.get("detail", "")

        if mode == "HOTEL":
            identifier = r.get("leg_request_id", "N/A")
            lines.append(f"\n{icon} Hotel  [{identifier}]")
        elif mode == "CAR":
            identifier = r.get("cab_id", "N/A")
            lines.append(f"\n{icon} Car    [cab_id={identifier}]")
        elif mode == "FLIGHT":
            req_id = r.get("cancellation_request_id")
            label = (
                f"request_id={req_id}" if req_id
                else f"trip={r.get('trip_id', trip_id)}"
            )
            lines.append(f"\n{icon} Flight [{label}]")
        else:
            lines.append(f"\n{icon} {mode}")

        lines.append(f"   Status : {status}")
        if detail:
            lines.append(f"   Detail : {detail}")

    # Counts
    total = len(results)
    ok = sum(
        1 for r in results if r.get("status") in ("cancelled", "submitted")
    )
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")

    lines.append("")
    lines.append("=" * 50)
    lines.append(
        f"Total: {total} leg(s) processed — "
        f"{ok} succeeded, {failed} failed, {skipped} skipped."
    )
    if failed:
        lines.append(
            "⚠ Some legs could not be cancelled automatically. "
            "Please contact support for assistance."
        )

    return "\n".join(lines)
