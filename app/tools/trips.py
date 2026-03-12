import logging
from datetime import datetime, timezone

import app.config as _config
from app.config import API_BASE_URL, ENDPOINTS
from app.services import make_get_request

logger = logging.getLogger(__name__)

_MAX_TRIPS = 20
_PAGE_SIZE = 3


async def get_upcoming_trips() -> str:
    """Fetch the user's upcoming trips (up to 20, sorted by journey date).

    Call this tool whenever the user asks about their trips without
    providing a specific trip_id — for example:
      - "what trips do I have coming up?"
      - "cancel today's hotel booking"
      - "show me tomorrow's trip"
      - "what's my next flight?"

    Returns a summary table with trip_id, title, dates, status, and
    primary booking type. Use get_trip_itinerary on a specific trip_id
    for full details or before performing any cancel action.
    """
    auth_token = _config.get_user_access_token()
    headers = {"authorization": f"Bearer {auth_token}"}
    url = f"{API_BASE_URL}{ENDPOINTS['upcoming_trips']}"

    all_trips: list[dict] = []
    pages = _MAX_TRIPS // _PAGE_SIZE  # 2 pages

    for page in range(1, pages + 1):
        params = {
            "page_no": page,
            "limit": _PAGE_SIZE,
            "sort": "journey:asc",
        }
        data = await make_get_request(url, params=params, headers=headers)
        if not data or data.get("status_code") != 200:
            break
        items = data.get("data", [])
        all_trips.extend(items)
        pagination = data.get("pagination", {})
        if page >= (pagination.get("total_pages") or 1):
            break

    if not all_trips:
        return "No upcoming trips found."

    today = datetime.now(tz=timezone.utc).date()
    lines = [
        f"📅 Upcoming trips (showing {len(all_trips)}, "
        f"sorted by journey date) — today is {today}:\n",
    ]

    for item in all_trips:
        td = item.get("trip_details", {})
        trip_id = td.get("trip_id", "N/A")
        title = (
            td.get("title", {}).get("trip")
            or td.get("title", {}).get("default", "N/A")
        )
        status = td.get("status", "N/A")
        destination = td.get("destination", "N/A")

        # Friendly date range
        start_raw = td.get("min_date_utc", "")
        end_raw = td.get("max_date_utc", "")
        date_str = _fmt_date_range(start_raw, end_raw, today)

        # What type of bookings are in this trip
        all_legs = item.get("all_legs", {})
        types = _leg_types(all_legs)

        lines += [
            f"  Trip ID   : {trip_id}",
            f"  Title     : {title}",
            f"  Dates     : {date_str}",
            f"  Status    : {status}",
            f"  Where     : {destination}",
            f"  Contains  : {types}",
            "",
        ]

    lines.append(
        "Use get_trip_itinerary with the Trip ID above for full details "
        "or before cancelling a booking."
    )
    return "\n".join(lines)


def _fmt_date_range(
    start_raw: str, end_raw: str, today: "datetime.date"
) -> str:
    """Return a human-readable date range with relative labels."""
    def _parse(s: str) -> "datetime.date | None":
        if not s:
            return None
        try:
            # Handles ISO 8601 with offset e.g. "2026-03-19T16:00:00-04:00"
            return datetime.fromisoformat(s).date()
        except ValueError:
            return None

    start = _parse(start_raw)
    end = _parse(end_raw)

    def _label(d: "datetime.date | None") -> str:
        if d is None:
            return "N/A"
        delta = (d - today).days
        if delta == 0:
            return f"{d.strftime('%b %d')} (today)"
        if delta == 1:
            return f"{d.strftime('%b %d')} (tomorrow)"
        if delta == -1:
            return f"{d.strftime('%b %d')} (yesterday)"
        if 2 <= delta <= 6:
            return f"{d.strftime('%b %d')} (in {delta} days)"
        return d.strftime("%b %d, %Y")

    if start and end and start != end:
        return f"{_label(start)} → {_label(end)}"
    return _label(start)


def _leg_types(all_legs: dict) -> str:
    """Summarise booking types present in the trip."""
    parts = []
    type_map = {
        "flights": "✈ Flight",
        "hotels": "🏨 Hotel",
        "cars": "🚗 Car rental",
        "trains": "🚆 Train",
        "buses": "🚌 Bus",
    }
    for key, label in type_map.items():
        count = all_legs.get(key, {}).get("count", 0)
        if count:
            parts.append(f"{label} ×{count}")
    return ", ".join(parts) if parts else "N/A"


async def get_trips_by_user(user_id: str = "", status: str = "") -> str:
    """Fetch all trips for a specific user.

    Args:
        user_id: The unique identifier for the user. Defaults to the
                 currently authenticated user if not provided.
        status: Filter by status - upcoming, ongoing, completed,
                cancelled (optional)
    """
    if not user_id:
        user_id = _config.get_current_user_id()
    params: dict = {"user_id": user_id}
    if status:
        params["status"] = status

    url = f"{API_BASE_URL}{ENDPOINTS['trips']}"
    data = await make_get_request(url, params=params)

    if not data:
        return f"Unable to fetch trips for user '{user_id}'."

    return str(data)

