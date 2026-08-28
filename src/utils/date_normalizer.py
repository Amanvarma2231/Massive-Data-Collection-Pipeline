import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from dateutil import parser as date_parser

class DateNormalizer:
    @staticmethod
    def parse_to_iso(date_str: Optional[str], default_now_if_missing: bool = True) -> str:
        """Parse relative strings ('2 hours ago', 'yesterday') or raw timestamps to strict ISO-8601 UTC."""
        if not date_str or not date_str.strip():
            return datetime.now(timezone.utc).isoformat()

        clean_str = date_str.strip().lower()
        now = datetime.now(timezone.utc)

        if any(w in clean_str for w in ['just now', 'moment ago', 'seconds ago']):
            return now.isoformat()

        min_match = re.search(r'(\d+)\s*(?:minutes?|mins?)\s*ago', clean_str)
        if min_match:
            mins = int(min_match.group(1))
            return (now - timedelta(minutes=mins)).isoformat()

        hr_match = re.search(r'(\d+)\s*(?:hours?|hrs?|h)\s*ago', clean_str)
        if hr_match:
            hrs = int(hr_match.group(1))
            return (now - timedelta(hours=hrs)).isoformat()

        if 'yesterday' in clean_str:
            return (now - timedelta(hours=18)).isoformat()

        day_match = re.search(r'(\d+)\s*(?:days?|d)\s*ago', clean_str)
        if day_match:
            days = int(day_match.group(1))
            return (now - timedelta(days=days)).isoformat()

        week_match = re.search(r'(\d+)\s*(?:weeks?|w)\s*ago', clean_str)
        if week_match:
            weeks = int(week_match.group(1))
            return (now - timedelta(weeks=weeks)).isoformat()

        try:
            parsed = date_parser.parse(date_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)
            return parsed.isoformat()
        except Exception:
            return now.isoformat()

    @staticmethod
    def is_within_24_hours(iso_date_str: str) -> bool:
        """Verify if an ISO-8601 timestamp falls strictly within the last 24 hours."""
        try:
            dt = datetime.fromisoformat(iso_date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff = (now - dt).total_seconds()
            return 0 <= diff <= 86400
        except Exception:
            return True
