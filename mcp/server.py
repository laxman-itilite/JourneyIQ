import sys
import logging

from mcp.server.fastmcp import FastMCP

from app.tools.trips import get_trips, get_trip_details
from app.tools.bookings import create_booking, get_booking
from app.tools.cancellations import cancel_booking
from app.tools.policy import get_travel_policy, check_policy_compliance
from app.tools.faq import search_faq
from app.tools.expenses import get_expense_report
from app.tools.approvals import get_approval_status

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("itilite")


@mcp.tool()
async def trips_list(employee_id: str, status: str = "all") -> str:
    """List upcoming and past trips for an employee.

    Args:
        employee_id: The employee's ID
        status: Filter by trip status — "upcoming", "past", or "all" (default)
    """
    return await get_trips(employee_id=employee_id, status=status)


@mcp.tool()
async def trip_details(trip_id: str) -> str:
    """Get the full itinerary for a specific trip including flights, hotels, and car rentals.

    Args:
        trip_id: The trip ID
    """
    return await get_trip_details(trip_id=trip_id)


@mcp.tool()
async def booking_create(trip_id: str, segment_type: str, option_id: str, traveler_notes: str = "") -> str:
    """Initiate a booking request for a flight, hotel, or car rental on a trip.

    Args:
        trip_id: The trip ID to attach this booking to
        segment_type: One of "flight", "hotel", or "car"
        option_id: The selected option/inventory ID to book
        traveler_notes: Optional notes from the traveler
    """
    return await create_booking(trip_id=trip_id, segment_type=segment_type, option_id=option_id, traveler_notes=traveler_notes)


@mcp.tool()
async def booking_get(booking_id: str) -> str:
    """Retrieve the current status and full details of a booking.

    Args:
        booking_id: The booking ID
    """
    return await get_booking(booking_id=booking_id)


@mcp.tool()
async def booking_cancel(booking_id: str, reason: str = "") -> str:
    """Cancel a booking and get estimated refund information.

    Args:
        booking_id: The booking ID to cancel
        reason: Optional reason for cancellation
    """
    return await cancel_booking(booking_id=booking_id, reason=reason)


@mcp.tool()
async def policy_get(company_id: str, category: str) -> str:
    """Retrieve the company's travel policy rules for a given category.

    Args:
        company_id: The company ID
        category: One of "flights", "hotels", "car", "per_diem", or "general"
    """
    return await get_travel_policy(company_id=company_id, category=category)


@mcp.tool()
async def policy_check(company_id: str, segment_type: str, amount: float, currency: str = "USD", travel_class: str = "") -> str:
    """Validate whether a booking option complies with company travel policy.

    Args:
        company_id: The company ID
        segment_type: One of "flight", "hotel", or "car"
        amount: The booking amount
        currency: Currency code (default USD)
        travel_class: Travel class (e.g. "economy", "business") — optional
    """
    return await check_policy_compliance(
        company_id=company_id, segment_type=segment_type,
        amount=amount, currency=currency, travel_class=travel_class
    )


@mcp.tool()
async def faq_search(query: str) -> str:
    """Search Itilite platform FAQ for answers to product and process questions.

    Args:
        query: The question or topic to search for
    """
    return await search_faq(query=query)


@mcp.tool()
async def expense_report_get(trip_id: str, employee_id: str) -> str:
    """Retrieve submitted expense reports for a trip.

    Args:
        trip_id: The trip ID
        employee_id: The employee ID
    """
    return await get_expense_report(trip_id=trip_id, employee_id=employee_id)


@mcp.tool()
async def approval_status_get(entity_id: str, entity_type: str) -> str:
    """Check the approval workflow status for a trip or booking.

    Args:
        entity_id: The trip or booking ID
        entity_type: Either "trip" or "booking"
    """
    return await get_approval_status(entity_id=entity_id, entity_type=entity_type)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
