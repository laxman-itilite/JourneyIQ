import sys
import logging

from mcp.server.fastmcp import FastMCP

from app.tools import (
    register_hotel_tools,
    register_itinerary_tools,
    register_trip_tools,
    register_weather_tools,
)

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("itilite")

register_itinerary_tools(mcp)
register_hotel_tools(mcp)
register_trip_tools(mcp)
register_weather_tools(mcp)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
