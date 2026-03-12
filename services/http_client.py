import logging
from typing import Any

import httpx

from config import REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}


async def make_get_request(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
) -> dict[str, Any] | None:
    """Make an async GET request with error handling."""
    req_headers = {**_DEFAULT_HEADERS, **(headers or {})}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers=req_headers,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP %s for GET %s", e.response.status_code, url)
        except Exception as e:
            logger.error("GET %s failed: %s", url, e)
    return None


async def make_post_request(
    url: str,
    payload: dict,
    headers: dict | None = None,
) -> dict[str, Any] | None:
    """Make an async POST request with error handling."""
    req_headers = {
        **_DEFAULT_HEADERS,
        "Content-Type": "application/json",
        **(headers or {}),
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, json=payload, headers=req_headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP %s for POST %s", e.response.status_code, url)
        except Exception as e:
            logger.error("POST %s failed: %s", url, e)
    return None


async def make_put_request(
    url: str,
    payload: dict,
    headers: dict | None = None,
) -> dict[str, Any] | None:
    """Make an async PUT request with error handling."""
    req_headers = {
        **_DEFAULT_HEADERS,
        "Content-Type": "application/json",
        **(headers or {}),
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                url, json=payload, headers=req_headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP %s for PUT %s", e.response.status_code, url)
        except Exception as e:
            logger.error("PUT %s failed: %s", url, e)
    return None
