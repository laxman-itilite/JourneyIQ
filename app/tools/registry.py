"""Tool dispatch registry for the chat backend.

Maps Claude tool_use block names to their async handlers in tools/.
"""
from collections.abc import Callable

from .itinerary import get_trip_itinerary
from .trips import get_trips_by_user, get_upcoming_trips
from .hotels import get_hotel_details, cancel_hotel_booking, modify_hotel_booking
from .flights import (
    get_flight_cancellation_details,
    submit_flight_cancellation,
    get_flight_cancellation_status,
)
from .car_rental import cancel_car_booking

TOOL_REGISTRY: dict[str, Callable] = {
    "get_upcoming_trips": get_upcoming_trips,
    "get_trip_itinerary": get_trip_itinerary,
    # "get_trips_by_user": get_trips_by_user,
    "get_hotel_details": get_hotel_details,
    "cancel_hotel_booking": cancel_hotel_booking,
    "modify_hotel_booking": modify_hotel_booking,
    "get_flight_cancellation_details": get_flight_cancellation_details,
    "submit_flight_cancellation": submit_flight_cancellation,
    "get_flight_cancellation_status": get_flight_cancellation_status,
    "cancel_car_booking": cancel_car_booking,
}


async def dispatch(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name with the given input dict."""
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        return f"Unknown tool: '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"
    try:
        return await handler(**tool_input)
    except Exception as exc:
        return f"Tool '{tool_name}' failed: {exc}"
