import logging

from mcp.server.fastmcp import FastMCP

from config import API_BASE_URL, ENDPOINTS
from services import make_get_request

logger = logging.getLogger(__name__)


def register_itinerary_tools(mcp: FastMCP) -> None:
    """Register all itinerary-related tools."""

    @mcp.tool()
    async def get_trip_itinerary(trip_id: str) -> str:
        """Get the full itinerary for a specific trip.

        Args:
            trip_id: The unique identifier for the trip (e.g. "TRIP123")
        """
        url = f"{API_BASE_URL}{ENDPOINTS['itinerary'].format(trip_id=trip_id)}"
        data = await make_get_request(url)

        if not data:
            return f"Unable to fetch itinerary for trip '{trip_id}'."

        # TODO: format response once real API shape is known
        return str(data)
