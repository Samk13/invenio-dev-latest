#!/usr/bin/env python3
"""Cleanup open InvenioRDM community requests via REST API."""

# Example usage:
# export INVENIO_API_TOKEN='...'
# uv run python scripts/devTools/cleanup_community_requests.py <community_id> --action cancel


import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

# -----------------------------------------------------------------------------
# Config variables (keep everything configurable here first)
# -----------------------------------------------------------------------------
BASE_URL = os.getenv("INVENIO_BASE_URL", "https://127.0.0.1:5000").rstrip("/")
API_TOKEN_ENV_VAR = "INVENIO_API_TOKEN"
REQUESTS_ENDPOINT = "/api/requests"
ACTION_MESSAGE = "handled with script"
ACTION_MESSAGE_FORMAT = "html"
DEFAULT_ACTION = "decline"  # Supported: accept, cancel, decline
REQUEST_TIMEOUT_SECONDS = 30
PAGE_SIZE = 100
OPEN_STATUSES = {"open", "created", "submitted"}
VERIFY_TLS = os.getenv("INVENIO_VERIFY_TLS", "false").lower() in ("1", "true", "yes")


def _ssl_context(verify_tls):
    if verify_tls:
        return None
    return ssl._create_unverified_context()  # nosec B323


def _api_request(method, url, token, timeout, verify_tls, payload=None):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, method=method, headers=headers, data=data)
    context = _ssl_context(verify_tls)

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read().decode("utf-8").strip()
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"{method} {url} failed: {error}") from error


def _iter_requests(base_url, token, timeout, page_size, verify_tls):
    next_url = f"{base_url}{REQUESTS_ENDPOINT}?page=1&size={page_size}"
    while next_url:
        response = _api_request("GET", next_url, token, timeout, verify_tls)
        hits = response.get("hits", {}).get("hits", [])
        for hit in hits:
            yield hit

        next_link = response.get("links", {}).get("next")
        if not next_link:
            break
        if next_link.startswith("http"):
            next_url = next_link
        else:
            next_url = urllib.parse.urljoin(base_url, next_link)


def _extract_community_id(request_obj):
    receiver = request_obj.get("receiver") or {}
    community_value = receiver.get("community")
    if isinstance(community_value, dict):
        if community_value.get("id"):
            return str(community_value["id"])
    elif community_value:
        return str(community_value)
    if receiver.get("id"):
        return str(receiver["id"])

    topic = request_obj.get("topic") or {}
    parent = topic.get("parent") or {}
    parent_communities = parent.get("communities") or {}
    if parent_communities.get("default"):
        return str(parent_communities["default"])
    topic_communities = topic.get("communities") or {}
    if topic_communities.get("default"):
        return str(topic_communities["default"])
    return None


def _is_open_request(request_obj):
    if "is_open" in request_obj:
        return bool(request_obj.get("is_open"))
    status = str(request_obj.get("status", "")).lower().strip()
    if not status:
        return True
    return status in OPEN_STATUSES


def _run_request_action(base_url, token, request_id, action, timeout, verify_tls):
    url = f"{base_url}{REQUESTS_ENDPOINT}/{request_id}/actions/{action}"
    payload = None
    if action in {"cancel", "decline"}:
        payload = {
            "payload": {
                "content": ACTION_MESSAGE,
                "format": ACTION_MESSAGE_FORMAT,
            }
        }
    _api_request("POST", url, token, timeout, verify_tls, payload=payload)
    verb = {"accept": "Accepted", "cancel": "Canceled", "decline": "Declined"}[action]
    print(f"{verb} request {request_id}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find open requests for one community and cleanup them."
    )
    parser.add_argument("community_id", help="Community id to match.")
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"InvenioRDM base URL (default: {BASE_URL})",
    )
    parser.add_argument(
        "--token",
        default=os.getenv(API_TOKEN_ENV_VAR, ""),
        help=f"API token (default: ${API_TOKEN_ENV_VAR})",
    )
    parser.add_argument(
        "--action",
        choices=["accept", "cancel", "decline"],
        default=DEFAULT_ACTION,
        help=f"Cleanup action (default: {DEFAULT_ACTION})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=REQUEST_TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds (default: {REQUEST_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--verify-tls",
        action="store_true",
        default=VERIFY_TLS,
        help=(
            "Verify TLS certificates (default: disabled for localhost/self-signed certs)."
        ),
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=PAGE_SIZE,
        help=f"Requests page size (default: {PAGE_SIZE})",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    token = args.token.strip()
    if not token:
        print(
            f"Missing token. Export it first, e.g. export {API_TOKEN_ENV_VAR}=<token>",
            file=sys.stderr,
        )
        return 1

    base_url = args.base_url.rstrip("/")
    scanned = 0
    matched_community = 0
    matched_open = 0
    changed = 0
    failures = 0

    for request_obj in _iter_requests(
        base_url, token, args.timeout, args.page_size, args.verify_tls
    ):
        scanned += 1
        request_id = str(request_obj.get("id", ""))
        community_id = _extract_community_id(request_obj)
        if community_id != args.community_id:
            continue

        matched_community += 1
        if not _is_open_request(request_obj):
            continue

        matched_open += 1
        try:
            _run_request_action(
                base_url, token, request_id, args.action, args.timeout, args.verify_tls
            )
            changed += 1
        except Exception as error:  # pylint: disable=broad-exception-caught
            failures += 1
            print(f"Failed request {request_id}: {error}", file=sys.stderr)

    print(
        "Summary: scanned={}, community_matched={}, open_matched={}, changed={}, "
        "failures={}, action={}".format(
            scanned,
            matched_community,
            matched_open,
            changed,
            failures,
            args.action,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
