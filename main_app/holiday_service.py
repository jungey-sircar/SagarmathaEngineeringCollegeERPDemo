from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from typing import Any

import requests
from bs4 import BeautifulSoup

MONTH_TO_NUMBER = {
    "Baisakh": 1,
    "Baishakh": 1,
    "Jestha": 2,
    "Ashadh": 3,
    "Shrawan": 4,
    "Bhadra": 5,
    "Ashwin": 6,
    "Kartik": 7,
    "Mangsir": 8,
    "Poush": 9,
    "Magh": 10,
    "Falgun": 11,
    "Chaitra": 12,
}

NUMBER_TO_MONTH = {
    value: key
    for key, value in MONTH_TO_NUMBER.items()
    if key == value or key == "Baishakh"
}
NUMBER_TO_MONTH.update(
    {
        2: "Jestha",
        3: "Ashadh",
        4: "Shrawan",
        5: "Bhadra",
        6: "Ashwin",
        7: "Kartik",
        8: "Mangsir",
        9: "Poush",
        10: "Magh",
        11: "Falgun",
        12: "Chaitra",
    }
)

OPTIONAL_KEYWORDS = (
    "महिला",
    "कर्मचारी",
    "समुदाय",
    "सम्बन्धित",
    "विशेष क्षमता",
    "उपत्यका",
    "नेवा",
    "किराँत",
    "पर्व मनाउने",
    "लाई मात्र",
    "लाई बिदा",
    "लाई विदा",
    "लागि मात्र",
    "छुट्टी",
)

OPTIONAL_EXACT_NAMES = (
    "हरितालिका तीज",
    "गाईजात्रा",
    "जितियापर्व",
    "इन्द्रजात्रा",
    "भोटो जात्रा",
    "गोरखकाली पूजा",
    "उधौली पर्व",
    "उभौली पर्व",
)

HOLIDAY_SOURCE_URL = (
    "https://raw.githubusercontent.com/bikrantj/nepali-calendar-scraper/main/data.json"
)
LIVE_CALENDAR_SOURCE_URL = "https://nepalicalendar.rat32.com/index_nep.php"

LIVE_SOURCE_YEARS = {2083, 2084}

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def estimate_bs_year(reference_date: date | None = None) -> int:
    reference_date = reference_date or date.today()
    nepali_new_year_start = (4, 14)
    if (reference_date.month, reference_date.day) >= nepali_new_year_start:
        return reference_date.year + 57
    return reference_date.year + 56


def _clean_text(value):
    return " ".join(str(value or "").split())


def _parse_day_number(value):
    cleaned_value = _clean_text(value).translate(DEVANAGARI_DIGITS)
    try:
        return int(cleaned_value)
    except (TypeError, ValueError):
        return None


def _extract_text(node):
    if node is None:
        return ""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _is_red_day(node):
    if node is None:
        return False
    font = node.find("font")
    return bool(font and _clean_text(font.get("color")).lower() == "red")


def _month_name(month_number: int) -> str:
    if month_number == 1:
        return "Baisakh"
    return NUMBER_TO_MONTH.get(month_number, "Baisakh")


def _looks_like_artifact_payload(payload: Any) -> bool:
    if not isinstance(payload, dict) or not payload:
        return False

    first_value = next(iter(payload.values()))
    return isinstance(first_value, dict) and "nepali_date" in first_value


def _build_artifact_rows(payload: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for _, day_data in payload.items():
        nepali_date = _clean_text(day_data.get("nepali_date"))
        if not nepali_date:
            continue

        parts = nepali_date.split("/")
        if len(parts) != 3:
            continue

        try:
            bs_year, month_number, day_number = (int(part) for part in parts)
        except ValueError:
            continue

        raw_events = day_data.get("events") or []
        if not isinstance(raw_events, list):
            raw_events = [raw_events]
        events = [_clean_text(event) for event in raw_events if _clean_text(event)]

        if events:
            event_name = " / ".join(events)
        else:
            event_name = nepali_date

        rows.append(
            {
                "name": event_name,
                "from": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                "to": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                "remarks": event_name,
                "holiday": bool(day_data.get("is_public_holiday")),
                "specialday": bool(day_data.get("specialday")),
                "events": events,
            }
        )

    rows.sort(key=lambda item: item["from"])
    return rows


def _parse_live_month(bs_year: int, month_number: int):
    response = requests.post(
        LIVE_CALENDAR_SOURCE_URL,
        data={
            "selYear": str(bs_year),
            "selMonth": str(month_number),
            "viewCalander": "View+Calander",
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    month_rows: list[dict[str, Any]] = []

    for cell in soup.select(".cells"):
        cell_soup = BeautifulSoup(str(cell), "html.parser")
        day_node = cell_soup.select_one("#nday")
        day_number = _parse_day_number(_extract_text(day_node))
        if day_number is None:
            continue

        holiday_name = _clean_text(_extract_text(cell_soup.select_one("#fest")))
        tithi_text = _clean_text(_extract_text(cell_soup.select_one("#dashi")))
        english_day = _clean_text(_extract_text(cell_soup.select_one("#eday")))
        holiday = _is_red_day(day_node)

        if not holiday_name and not holiday:
            continue

        row_name = (
            holiday_name
            or tithi_text
            or f"{bs_year}/{month_number:02d}/{day_number:02d}"
        )
        month_rows.append(
            {
                "name": row_name,
                "from": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                "to": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                "remarks": holiday_name or tithi_text or english_day,
                "holiday": holiday,
                "specialday": bool(holiday_name and not holiday),
                "events": [holiday_name] if holiday_name else [],
            }
        )

    return month_rows


def _load_live_year_data(bs_year: int):
    rows: list[dict[str, Any]] = []
    for month_number in range(1, 13):
        rows.extend(_parse_live_month(bs_year, month_number))

    rows.sort(key=lambda item: item["from"])
    return rows


@lru_cache(maxsize=16)
def _load_year_data(bs_year: int):
    if bs_year in LIVE_SOURCE_YEARS:
        try:
            return _load_live_year_data(bs_year)
        except Exception:
            pass

    artifact_url = (
        "https://raw.githubusercontent.com/casualsnek/npEventsAPI/main/artifacts/"
        f"artifact-{bs_year}.json"
    )
    try:
        response = requests.get(artifact_url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and payload:
            return payload
    except Exception:
        pass

    response = requests.get(HOLIDAY_SOURCE_URL, timeout=15)
    response.raise_for_status()
    payload = response.json()

    year_data = payload.get(str(bs_year), {})
    if not isinstance(year_data, dict):
        return {}
    return year_data


def _flatten_year(bs_year: int):
    payload = _load_year_data(bs_year)
    if isinstance(payload, list):
        return payload

    if _looks_like_artifact_payload(payload):
        return _build_artifact_rows(payload)

    rows = []

    for month_name, days in payload.items():
        month_number = MONTH_TO_NUMBER.get(month_name)
        if not month_number or not isinstance(days, list):
            continue

        for day_data in days:
            day_number = _parse_day_number(day_data.get("nepaliDay"))
            event_name = _clean_text(day_data.get("event"))
            if day_number is None:
                continue

            if not event_name:
                event_name = _clean_text(day_data.get("nepaliFullDate"))
            if not event_name:
                continue

            rows.append(
                {
                    "name": event_name,
                    "from": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                    "to": f"{bs_year}/{month_number:02d}/{day_number:02d}",
                    "remarks": event_name,
                    "holiday": bool(
                        day_data.get("isHoliday") or day_data.get("holiday")
                    ),
                    "specialday": bool(day_data.get("specialday")),
                    "events": [event_name],
                }
            )

    rows.sort(key=lambda item: item["from"])
    return rows


def _is_optional_holiday(row):
    if row.get("holiday"):
        return False

    event_name = row["name"].lower()
    if row.get("specialday"):
        return True

    if row.get("events"):
        return True

    if any(name.lower() in event_name for name in OPTIONAL_EXACT_NAMES):
        return True

    return any(keyword.lower() in event_name for keyword in OPTIONAL_KEYWORDS)


def get_nepali_holiday_dashboard_data(reference_date: date | None = None):
    current_bs_year = estimate_bs_year(reference_date)
    target_years = [current_bs_year]
    if current_bs_year in LIVE_SOURCE_YEARS:
        target_years.append(current_bs_year + 1)

    rows = []
    try:
        for bs_year in target_years:
            rows.extend(_flatten_year(bs_year))
    except Exception:
        pass

    rows.sort(key=lambda item: item["from"])

    holiday_rows = rows
    optional_holiday_rows = [row for row in rows if _is_optional_holiday(row)]

    if not holiday_rows and not optional_holiday_rows:
        holiday_rows = [
            {
                "name": "No holiday data available",
                "from": "-",
                "to": "-",
                "remarks": "API unavailable",
                "holiday": True,
                "specialday": False,
            },
        ]

    return {
        "holiday_period_label": f"BS {target_years[0]} to {target_years[-1]} holiday schedule",
        "holiday_rows": holiday_rows,
        "optional_holiday_rows": optional_holiday_rows,
    }
