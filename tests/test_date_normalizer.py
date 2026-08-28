import pytest
from datetime import datetime, timezone, timedelta
from src.utils.date_normalizer import DateNormalizer

def test_relative_date_parsing():
    now = datetime.now(timezone.utc)
    
    # 2 hours ago
    iso_2h = DateNormalizer.parse_to_iso("2 hours ago")
    dt_2h = datetime.fromisoformat(iso_2h)
    diff_2h = now - dt_2h
    assert 1.8 * 3600 <= diff_2h.total_seconds() <= 2.2 * 3600

    # 30 mins ago
    iso_30m = DateNormalizer.parse_to_iso("30 minutes ago")
    assert DateNormalizer.is_within_24_hours(iso_30m) is True

    # yesterday
    iso_yd = DateNormalizer.parse_to_iso("yesterday")
    assert DateNormalizer.is_within_24_hours(iso_yd) is True

def test_freshness_window():
    now = datetime.now(timezone.utc)
    
    recent_date = (now - timedelta(hours=5)).isoformat()
    assert DateNormalizer.is_within_24_hours(recent_date) is True
    
    old_date = (now - timedelta(hours=48)).isoformat()
    assert DateNormalizer.is_within_24_hours(old_date) is False
