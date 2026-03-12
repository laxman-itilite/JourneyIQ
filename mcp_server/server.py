import sys
import os
import logging

# Ensure the project root is on sys.path when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

from app.tools.registry import TOOL_REGISTRY

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("itilite")

for _fn in TOOL_REGISTRY.values():
    mcp.tool()(_fn)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
