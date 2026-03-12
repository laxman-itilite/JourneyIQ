import logging

import app.config as _config
from app.config import API_BASE_URL, ENDPOINTS
from app.services import make_get_request

logger = logging.getLogger(__name__)


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

