#!/usr/bin/env python3
"""
Comic Vine API client for fetching comic metadata.
"""

import re
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import get_api_key
from metadata import ComicMetadata

BASE_URL = "https://comicvine.gamespot.com/api"


class ComicVineClient:
    """Client for Comic Vine API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError("Comic Vine API key is required")
    
    def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make an API request."""
        params = params or {}
        params["api_key"] = self.api_key
        params["format"] = "json"
        
        url = f"{BASE_URL}/{endpoint}"
        headers = {
            "User-Agent": "BD-Library-Manager/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("status_code") != 1:
            error = data.get("error", "Unknown error")
            raise Exception(f"Comic Vine API error: {error} (code: {data.get('status_code')})")
        
        return data
    
    def search_series(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for a comic series.
        
        Returns list of matching series with basic info.
        """
        data = self._request("search", {
            "query": query,
            "resources": "volume",
            "limit": limit
        })
        
        results = []
        for item in data.get("results", []):
            results.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "publisher": item.get("publisher", {}).get("name") if isinstance(item.get("publisher"), dict) else item.get("publisher"),
                "start_year": item.get("start_year"),
                "image": item.get("image", {}).get("small_url") if isinstance(item.get("image"), dict) else None,
                "count_of_issues": item.get("count_of_issues"),
            })
        
        return results
    
    def get_volume(self, volume_id: int) -> Dict[str, Any]:
        """Get detailed volume information."""
        data = self._request(f"volume/4050-{volume_id}")
        return data.get("results", {})
    
    def get_volume_issues(self, volume_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all issues for a volume.
        
        Note: Comic Vine has a limit of 100 per request, use offset for more.
        """
        issues = []
        offset = 0
        
        while True:
            data = self._request(f"issues", {
                "filter": f"volume:{volume_id}",
                "limit": limit,
                "offset": offset,
                "sort": "issue_number:asc"
            })
            
            results = data.get("results", [])
            if not results:
                break
                
            for issue in results:
                issues.append({
                    "id": issue.get("id"),
                    "issue_number": issue.get("issue_number"),
                    "name": issue.get("name"),
                    "cover_date": issue.get("cover_date"),
                    "store_date": issue.get("store_date"),
                    "description": issue.get("description"),
                    "image": issue.get("image", {}).get("small_url") if isinstance(issue.get("image"), dict) else None,
                })
            
            offset += limit
            if len(results) < limit:
                break
        
        return issues
    
    def get_issue(self, issue_id: int) -> Dict[str, Any]:
        """Get detailed issue information including credits."""
        
        issue_id = f"4000-{issue_id}"

        data = self._request(f"issue/{issue_id}", {
            "field_list": ",".join([
                "id", "issue_number", "name", "cover_date", "store_date",
                "description", "image", "volume", "person_credits",
                "character_credits", "team_credits", "location_credits",
                "site_detail_url"
            ])
        })

        return data.get("results", {})

def map_to_comicinfo(issue_data: Dict[str, Any], volume_data: Optional[Dict[str, Any]] = None) -> ComicMetadata:
    """
    Map Comic Vine issue data to ComicMetadata.
    
    Args:
        issue_data: Full issue data from Comic Vine
        volume_data: Optional volume data for additional context
    
    Returns:
        ComicMetadata object
    """
    result = ComicMetadata()
    
    # Summary/Description - strip HTML tags
    description = issue_data.get("description", "")
    if description:
        description = re.sub(r'<[^>]+>', '', description)
        result.summary = description.strip()
    
    # Parse cover date
    cover_date = issue_data.get("cover_date")
    if cover_date:
        try:
            dt = datetime.strptime(cover_date, "%Y-%m-%d")
            result.year = dt.year
            result.month = dt.month
            result.day = dt.day
        except ValueError:
            pass
    
    # Web URL from Comic Vine
    cv_url = issue_data.get("site_detail_url")
    if cv_url:
        result.web = cv_url
        result.notes = f"Comic Vine: {cv_url}"
    
    # Extract person credits by role
    person_credits = issue_data.get("person_credits", [])
    roles_map = {
        "writer": "writer",
        "artist": "artist",  # Comic Vine uses "artist" for penciller
        "penciller": "artist",
        "inker": "inker",
        "colorist": "colorist",
        "letterer": "letterer",
        "cover": "cover_artist",
        "editor": "editor",
    }
    
    people_by_role = {}
    for person in person_credits:
        role_str = person.get("role", "")
        name = person.get("name", "")
        if role_str and name:
            # Split comma-separated roles
            roles = [r.strip().lower() for r in role_str.split(',')]
            for role in roles:
                if role not in people_by_role:
                    people_by_role[role] = []
                people_by_role[role].append(name)
    
    for cv_role, ci_field in roles_map.items():
        if cv_role in people_by_role:
            setattr(result, ci_field, ", ".join(people_by_role[cv_role]))
    
    # Publisher from volume
    if volume_data:
        publisher = volume_data.get("publisher", {})
        if isinstance(publisher, dict):
            result.publisher = publisher.get("name")
        elif publisher:
            result.publisher = publisher
    
    # Genre from volume
    if volume_data:
        genre = volume_data.get("genre")
        if genre:
            result.genre = genre
    
    # Count of issues from volume
    if volume_data:
        count = volume_data.get("count_of_issues")
        if count:
            result.count = count
    
    return result


def normalize_issue_number(num: str) -> str:
    """Normalize Comic Vine issue numbers."""
    num = str(num).lower().strip()
    num = re.sub(r'[#\s]', '', num)      # remove # and spaces
    num = re.sub(r'\(.*?\)', '', num)    # remove "(of 6)" etc
    return num


def find_issue_by_number(
    issues: List[Dict[str, Any]], number: str
) -> Optional[Dict[str, Any]]:
    """Find an issue by its number."""
    
    search_num = normalize_issue_number(number)

    for issue in issues:
        issue_num = normalize_issue_number(issue.get("issue_number", ""))

        # Exact match
        if issue_num == search_num:
            return issue

        # Match base number (handles 1A when searching 1)
        base_issue = re.match(r"\d+", issue_num)
        if base_issue and base_issue.group() == search_num:
            return issue

    return None
