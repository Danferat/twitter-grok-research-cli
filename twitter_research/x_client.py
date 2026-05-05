from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class XApiError(RuntimeError):
    """Raised when X API rejects or fails a request."""


def choose_search_mode(days: int, mode: str) -> str:
    if mode not in {"auto", "recent", "all"}:
        raise ValueError("mode must be auto, recent, or all")
    if mode == "auto":
        return "recent" if days <= 7 else "all"
    return mode


class XClient:
    base_url = "https://api.twitter.com"

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    def build_search_url(
        self,
        query: str,
        days: int,
        limit: int,
        mode: str = "auto",
        next_token: str | None = None,
    ) -> str:
        selected_mode = choose_search_mode(days=days, mode=mode)
        endpoint = "/2/tweets/search/recent" if selected_mode == "recent" else "/2/tweets/search/all"
        max_results = max(10, min(limit, 100))
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        params = {
            "query": query,
            "max_results": str(max_results),
            "tweet.fields": "author_id,created_at,lang,public_metrics,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics",
            "start_time": start_time.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if next_token:
            params["next_token"] = next_token
        return f"{self.base_url}{endpoint}?{urlencode(params)}"

    def search(self, query: str, days: int, limit: int, mode: str = "auto") -> dict[str, Any]:
        if days < 1:
            raise ValueError("days must be at least 1")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        selected_mode = choose_search_mode(days=days, mode=mode)
        collected: list[dict[str, Any]] = []
        users: list[dict[str, Any]] = []
        meta: dict[str, Any] = {}
        next_token: str | None = None

        while len(collected) < limit:
            page_limit = min(100, limit - len(collected))
            url = self.build_search_url(query, days, page_limit, selected_mode, next_token)
            page = self._get_json(url)
            collected.extend(page.get("data", []))
            users.extend(page.get("includes", {}).get("users", []))
            meta = page.get("meta", {})
            next_token = meta.get("next_token")
            if not next_token:
                break

        return {
            "data": collected[:limit],
            "includes": {"users": users},
            "meta": meta,
        }

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "twitter-research-cli/0.1",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise XApiError(f"X API returned HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise XApiError(f"Could not reach X API: {exc.reason}") from exc
