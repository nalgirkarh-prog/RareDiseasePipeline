"""
utils/http.py

Shared, robust HTTP layer for every client in the pipeline.

Why this exists
---------------
The original clients each called ``requests.get(...)`` directly with:
  - no timeout        -> a hung server freezes the whole pipeline
  - no retries        -> one transient 5xx / network blip kills a 15-stage run
  - no backoff        -> NCBI throttles you (HTTP 429) and the run dies
  - no shared session -> no connection reuse, no consistent User-Agent

This module centralises all of that. Every client should import and use
``get_json`` / ``get_text`` instead of calling requests directly.

Environment variables (all optional)
-------------------------------------
  NCBI_API_KEY   - if set, NCBI E-utilities requests get 10 req/s instead of 3.
  NCBI_EMAIL     - contact email sent to NCBI (politeness / unblocking).
  HTTP_TIMEOUT   - per-request timeout in seconds (default 30).
  HTTP_RETRIES   - number of retry attempts on transient failures (default 4).
"""

from __future__ import annotations

import os
import time
import requests
from requests.adapters import HTTPAdapter

try:
    # urllib3 ships with requests; Retry lives here.
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover - extremely unlikely
    Retry = None


# ----------------------------------------------------------------------
# Configuration (read once, at import time)
# ----------------------------------------------------------------------

DEFAULT_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "30"))
DEFAULT_RETRIES = int(os.environ.get("HTTP_RETRIES", "4"))

USER_AGENT = (
    "RareDiseasePipeline/1.0 "
    "(research; https://github.com/; "
    f"mailto:{os.environ.get('NCBI_EMAIL', 'unknown@example.org')})"
)


# ----------------------------------------------------------------------
# Session factory with automatic retry / backoff
# ----------------------------------------------------------------------

def build_session(retries: int = DEFAULT_RETRIES) -> requests.Session:
    """Return a requests.Session with retry+backoff mounted on http/https."""

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    if Retry is not None:
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=1.0,               # 0s, 1s, 2s, 4s, 8s ...
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

    return session


# A single module-level session, reused across all clients (connection pooling).
_SESSION = build_session()


# ----------------------------------------------------------------------
# NCBI helper: inject api_key / email automatically
# ----------------------------------------------------------------------

def _augment_ncbi_params(url: str, params: dict | None) -> dict:
    """Add NCBI api_key + email to E-utilities calls when available."""
    params = dict(params or {})
    if "eutils.ncbi.nlm.nih.gov" in url:
        api_key = os.environ.get("NCBI_API_KEY")
        email = os.environ.get("NCBI_EMAIL")
        if api_key and "api_key" not in params:
            params["api_key"] = api_key
        if email and "email" not in params:
            params["email"] = email
        params.setdefault("tool", "RareDiseasePipeline")
    return params


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

class HTTPError(RuntimeError):
    """Raised when a request ultimately fails after all retries."""


def get(url, params=None, timeout=DEFAULT_TIMEOUT, session=None, **kwargs):
    """
    Perform a GET with retries, backoff, timeout and a friendly error.

    Raises HTTPError with a readable message on failure, instead of leaking
    a raw requests exception that is hard to act on.
    """
    session = session or _SESSION
    params = _augment_ncbi_params(url, params)

    try:
        response = session.get(
            url,
            params=params,
            timeout=timeout,
            **kwargs,
        )
    except requests.exceptions.RequestException as exc:
        raise HTTPError(f"Network error contacting {url}: {exc}") from exc

    if response.status_code >= 400:
        # give the caller the status + a snippet of the body to debug with
        snippet = (response.text or "")[:200].replace("\n", " ")
        raise HTTPError(
            f"{url} returned HTTP {response.status_code}. Body: {snippet}"
        )

    return response


def get_json(url, params=None, timeout=DEFAULT_TIMEOUT, session=None, **kwargs):
    """GET a URL and return parsed JSON, or raise HTTPError on bad JSON."""
    response = get(url, params=params, timeout=timeout, session=session, **kwargs)
    try:
        return response.json()
    except ValueError as exc:
        snippet = (response.text or "")[:200].replace("\n", " ")
        raise HTTPError(
            f"Expected JSON from {url} but could not parse it. Body: {snippet}"
        ) from exc


def get_text(url, params=None, timeout=DEFAULT_TIMEOUT, session=None, **kwargs):
    """GET a URL and return the raw text body."""
    response = get(url, params=params, timeout=timeout, session=session, **kwargs)
    return response.text


def polite_pause(seconds: float = 0.34) -> None:
    """
    Sleep between NCBI calls. Without an API key NCBI allows 3 req/s,
    so ~0.34s between calls keeps you under the limit. With a key you
    can lower this.
    """
    time.sleep(seconds)
