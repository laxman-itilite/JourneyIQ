import logging

from mcp.server.fastmcp import FastMCP

from config import API_BASE_URL, ENDPOINTS
from services import make_get_request

logger = logging.getLogger(__name__)


def register_trip_tools(mcp: FastMCP) -> None:
    """Register all trip-related tools."""

    @mcp.tool()
    async def get_trips_by_user(user_id: str, status: str = "") -> str:
        """Fetch all trips for a specific user.

        Args:
            user_id: The unique identifier for the user (e.g. "USR001")
            status: Filter by status - upcoming, ongoing, completed,
                    cancelled (optional)
        """
        params: dict = {"user_id": user_id}
        if status:
            params["status"] = status

        url = f"{API_BASE_URL}{ENDPOINTS['trips']}"
        data = await make_get_request(url, params=params)

        if not data:
            return f"Unable to fetch trips for user '{user_id}'."

        # TODO: format response once real API shape is known
        return str(data)
