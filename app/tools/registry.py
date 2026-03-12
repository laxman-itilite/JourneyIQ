"""Tool dispatch registry.

Maps tool names (as returned by Claude's tool_use blocks) to their async handlers.
Add new tools here when extending the assistant's capabilities.
"""
from collections.abc import Callable

from app.tools.trips import get_trips, get_trip_details
from app.tools.bookings import create_booking, get_booking
from app.tools.cancellations import cancel_booking
from app.tools.policy import get_travel_policy, check_policy_compliance
from app.tools.faq import search_faq
from app.tools.expenses import get_expense_report
from app.tools.approvals import get_approval_status

TOOL_REGISTRY: dict[str, Callable] = {
    "get_trips": get_trips,
    "get_trip_details": get_trip_details,
    "create_booking": create_booking,
    "get_booking": get_booking,
    "cancel_booking": cancel_booking,
    "get_travel_policy": get_travel_policy,
    "check_policy_compliance": check_policy_compliance,
    "search_faq": search_faq,
    "get_expense_report": get_expense_report,
    "get_approval_status": get_approval_status,
}


async def dispatch(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name with the given input dict.

    Returns a string result (JSON or plain text) to send back to Claude.
    """
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        return f"Unknown tool: '{tool_name}'. Available tools: {list(TOOL_REGISTRY.keys())}"
    try:
        return await handler(**tool_input)
    except Exception as exc:
        return f"Tool '{tool_name}' failed: {exc}"
