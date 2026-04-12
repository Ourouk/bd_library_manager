#!/usr/bin/env python3
"""
Comic Vine API client for fetching comic metadata.
"""

import re
from datetime import datetime
from typing import Any

import requests

from bdlib.config import get_api_key
from bdlib.dto import ComicMetadata
from bdlib.log import get_logger

logger = get_logger(__name__)

BASE_URL = "https://comicvine.gamespot.com/api"


class ComicVineClient:
    """Client for Comic Vine API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError("Comic Vine API key is required")

    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make an API request."""
        params = params or {}
        params["api_key"] = self.api_key
        params["format"] = "json"

        url = f"{BASE_URL}/{endpoint}"
        headers = {"User-Agent": "BD-Library-Manager/1.0"}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status_code") != 1:
                error = data.get("error", "Unknown error")
                logger.error(f"Comic Vine API error: {error} (code: {data.get('status_code')})")
                return {}
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Comic Vine API: {e}")
            return {}

    def search_series(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search for a comic series.

        Returns list of matching series with basic info.
        """
        data = self._request("search", {"query": query, "resources": "volume", "limit": limit})
        return data.get("results", [])

    def get_volume(self, volume_id: int) -> dict[str, Any]:
        """Get detailed volume information."""
        data = self._request(f"volume/4050-{volume_id}")
        return data.get("results", {})

    def get_volume_issues(self, volume_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get all issues for a volume.

        Note: Comic Vine has a limit of 100 per request, use offset for more.
        """
        issues = []
        offset = 0
        while True:
            data = self._request(
                "issues",
                {"filter": f"volume:{volume_id}", "limit": limit, "offset": offset, "sort": "issue_number:asc"},
            )
            results = data.get("results", [])
            if not results:
                break
            issues.extend(results)
            offset += len(results)
            if len(results) < limit:
                break
        return issues

    def get_issue(self, issue_id: int) -> dict[str, Any]:
        """Get detailed issue information including credits."""
        issue_id_str = f"4000-{issue_id}"
        data = self._request(
            f"issue/{issue_id_str}",
            {
                "field_list": ",".join(
                    [
                        "id",
                        "issue_number",
                        "name",
                        "cover_date",
                        "store_date",
                        "description",
                        "image",
                        "volume",
                        "person_credits",
                        "character_credits",
                        "team_credits",
                        "location_credits",
                        "site_detail_url",
                    ]
                )
            },
        )
        return data.get("results", {})


def map_to_comicinfo(issue_data: dict[str, Any], volume_data: dict[str, Any] | None = None) -> ComicMetadata:
    """
    Map Comic Vine issue data to ComicMetadata.
    """
    result = ComicMetadata()

    if title := issue_data.get("name"):
        result.title = title

    if description := issue_data.get("description"):
        result.summary = re.sub(r"<[^>]+>", "", description).strip()

    if cover_date := issue_data.get("cover_date"):
        try:
            dt = datetime.strptime(cover_date, "%Y-%m-%d")
            result.year = dt.year
            result.month = dt.month
            result.day = dt.day
        except ValueError:
            pass

    if cv_url := issue_data.get("site_detail_url"):
        result.web = cv_url
        result.notes = f"Comic Vine: {cv_url}"

    person_credits = issue_data.get("person_credits", [])
    roles_map = {
        "writer": "writer",
        "artist": "artist",
        "penciller": "artist",
        "inker": "inker",
        "colorist": "colorist",
        "letterer": "letterer",
        "cover": "cover_artist",
        "editor": "editor",
    }
    people_by_role: dict[str, list[str]] = {}
    for person in person_credits:
        if role_str := person.get("role", ""):
            if name := person.get("name", ""):
                roles = [r.strip().lower() for r in role_str.split(",")]
                for role in roles:
                    people_by_role.setdefault(role, []).append(name)
    for cv_role, ci_field in roles_map.items():
        if cv_role in people_by_role:
            setattr(result, ci_field, ", ".join(people_by_role[cv_role]))

    if volume_data:
        if publisher := volume_data.get("publisher"):
            result.publisher = publisher.get("name") if isinstance(publisher, dict) else publisher
        if genre := volume_data.get("genre"):
            result.genre = genre
        if count := volume_data.get("count_of_issues"):
            result.count = count
    return result


def normalize_issue_number(num: str) -> str:
    """Normalize Comic Vine issue numbers."""
    num = str(num).lower().strip()
    num = re.sub(r"[#\s]", "", num)
    num = re.sub(r"\(.*?\)", "", num)
    return num


def find_issue_by_number(issues: list[dict[str, Any]], number: str) -> dict[str, Any] | None:
    """Find an issue by its number."""
    search_num = normalize_issue_number(number)
    for issue in issues:
        if issue_num := normalize_issue_number(issue.get("issue_number", "")):
            if issue_num == search_num:
                return issue
            if base_issue := re.match(r"\d+", issue_num):
                if base_issue.group() == search_num:
                    return issue
    return None


def confirm_series(client: ComicVineClient, series_name: str) -> dict | None:
    """Prompt user to confirm the correct series from search results."""
    logger.info(f"Searching Comic Vine for: {series_name}")
    results = client.search_series(series_name, limit=10)
    if not results:
        logger.warning("No results found.")
        return None

    print(f"  Found {len(results)} results:")
    for i, r in enumerate(results):
        publisher = f" ({r.get('publisher', {}).get('name', '')})" if r.get("publisher") else ""
        year = f" ({r.get('start_year', '')})" if r.get("start_year") else ""
        issues = f" [{r.get('count_of_issues', '?')} issues]" if r.get("count_of_issues") else ""
        volume_id = r.get("id", "")
        link = f" https://comicvine.gamespot.com/volume/4050-{volume_id}" if volume_id else ""
        print(f"    {i + 1}. {r['name']}{year}{publisher}{issues}{link}")

    print("    0. Skip (don't use Comic Vine)")
    print("    s. Skip all remaining (don't ask for this series again)")

    while True:
        choice = input(f"  Select series [1-{len(results)}]: ").strip().lower()
        if choice == "0":
            return None
        if choice == "s":
            return {"skip_all": True}
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                selected = results[idx]
                logger.info(f"Selected: {selected['name']}")
                return selected
        except ValueError:
            pass
        print(f"  Invalid choice. Enter a number 1-{len(results)} or 0 to skip.")
