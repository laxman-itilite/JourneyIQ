import logging
import sys

from mcp.server.fastmcp import FastMCP

from tools import (
    register_hotel_tools,
    register_itinerary_tools,
    register_trip_tools,
    register_weather_tools,
)

# Logging — stderr only (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

# ── MCP Server ───────────────────────────────────────────────────────────────
mcp = FastMCP("JourneyIQ")

# ── Register Tools ───────────────────────────────────────────────────────────
register_itinerary_tools(mcp)
register_hotel_tools(mcp)
register_trip_tools(mcp)
register_weather_tools(mcp)

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

