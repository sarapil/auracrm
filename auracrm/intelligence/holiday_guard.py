# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P17 — Holiday Guard
Checks whether today is a public holiday in target countries before outreach.
Uses Nager.Date API for holiday data.
"""

import frappe
import requests
from frappe.utils import nowdate, add_days

NAGER_API = "https://date.nager.at/api/v3/PublicHolidays/{year}/{code}"

# Module-level cache (lives for the duration of the worker process)
_cache = {}


def is_working_day(target_countries: list) -> bool:
    """
    Returns False if today is a public holiday in ANY of the target countries.
    Used before any outreach or data enrichment operation.
    """
    if not target_countries:
        return True

    today = nowdate()
    year = today[:4]

    for code in target_countries:
        code = code.strip().upper()
        if not code:
            continue
        key = f"{code}_{year}"
        if key not in _cache:
            _cache[key] = _fetch_holidays(year, code)
        if today in _cache.get(key, []):
            return False

    return True


def get_next_working_day(target_countries: list) -> str:
    """Find the next day that is not a holiday in any target country."""
    check = add_days(nowdate(), 1)
    for _ in range(14):
        year = check[:4]
        is_holiday = False
        for code in target_countries:
            code = code.strip().upper()
            if not code:
                continue
            key = f"{code}_{year}"
            if key not in _cache:
                _cache[key] = _fetch_holidays(year, code)
            if check in _cache.get(key, []):
                is_holiday = True
                break
        if not is_holiday:
            return check
        check = add_days(check, 1)
    return check


def _fetch_holidays(year: str, country_code: str) -> list:
    """Fetch public holiday dates for a given year and country."""
    try:
        r = requests.get(
            NAGER_API.format(year=year, code=country_code),
            timeout=10,
        )
        if r.status_code == 200:
            return [h["date"] for h in r.json()]
    except Exception:
        pass
    return []


def clear_cache():
    """Clear holiday cache — scheduled weekly or at start of new year."""
    global _cache
    _cache = {}
