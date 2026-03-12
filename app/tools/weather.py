import logging

from app.services import make_get_request

logger = logging.getLogger(__name__)

NWS_API_BASE = "https://api.weather.gov"


async def get_weather_alerts(state: str) -> str:
    """Get active weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_get_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return f"No active alerts for state '{state}'."

    alerts = [_format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location (e.g. 40.7128)
        longitude: Longitude of the location (e.g. -74.0060)
    """
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_get_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_get_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        temp = f"{period['temperature']}°{period['temperatureUnit']}"
        wind = f"{period['windSpeed']} {period['windDirection']}"
        forecasts.append(
            f"{period['name']}:\n"
            f"  Temperature : {temp}\n"
            f"  Wind        : {wind}\n"
            f"  Forecast    : {period['detailedForecast']}"
        )

    return "\n---\n".join(forecasts)


def _format_alert(feature: dict) -> str:
    props = feature["properties"]
    desc = props.get("description", "No description available")
    return (
        f"Event       : {props.get('event', 'Unknown')}\n"
        f"Area        : {props.get('areaDesc', 'Unknown')}\n"
        f"Severity    : {props.get('severity', 'Unknown')}\n"
        f"Description : {desc}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions')}"
    )
