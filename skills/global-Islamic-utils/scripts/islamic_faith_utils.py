#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
ALADHAN_BASE = "https://api.aladhan.com/v1"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"

# Calculation method per country (AlAdhan method IDs).
# Default fallback: 3 = Muslim World League.
COUNTRY_METHOD: Dict[str, int] = {
    "saudi arabia": 4,   # Umm al-Qura
    "makkah": 4,
    "egypt": 5,          # Egyptian General Authority of Survey
    "syria": 5,
    "sudan": 5,
    "libya": 5,
    "jordan": 23,        # Ministry of Awqaf Jordan
    "kuwait": 9,
    "qatar": 10,
    "uae": 16,
    "united arab emirates": 16,
    "turkey": 13,
    "russia": 14,
    "malaysia": 17,
    "indonesia": 20,
    "tunisia": 18,
    "algeria": 19,
    "morocco": 21,
    "singapore": 11,
    "france": 12,
    "portugal": 22,
    "united states": 2,   # ISNA — Islamic Society of North America
    "usa": 2,
    "us": 2,
    "canada": 2,
    "united kingdom": 15, # Moonsighting Committee Worldwide
    "uk": 15,
    "germany": 3,
    "iraq": 5,
    "lebanon": 5,
    "palestine": 5,
    "pakistan": 1,        # University of Islamic Sciences, Karachi
    "bangladesh": 1,
    "india": 1,
}

# Simple in-memory geocode cache to avoid duplicate Nominatim calls
_geocode_cache: Dict[str, tuple] = {}

# Gregorian month name → number, used for date extraction from news text
GREG_MONTHS_EN: Dict[str, int] = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "nov": 11, "dec": 12,
}
GREG_MONTHS_AR: Dict[str, int] = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4,
    "مايو": 5, "يونيو": 6, "يوليو": 7, "أغسطس": 8,
    "سبتمبر": 9, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
}
CITY_ALIASES = {
    "الرياض": "Riyadh",
    "riyadh": "Riyadh",
    "جدة": "Jeddah",
    "jeddah": "Jeddah",
    "مكة": "Makkah",
    "مكه": "Makkah",
    "makkah": "Makkah",
    "mecca": "Makkah",
    "المدينة": "Madinah",
    "المدينه": "Madinah",
    "madinah": "Madinah",
    "الدمام": "Dammam",
    "الخبر": "Khobar",
    "الطائف": "Taif",
    "أبها": "Abha",
    "تبوك": "Tabuk",
    "حائل": "Hail",
    "جازان": "Jazan",
    "نجران": "Najran",
    "بريدة": "Buraidah",
}

DAY_INFO: Dict[str, Dict[str, Any]] = {
    "Sunday": {
        "name_ar": "الأحد",
        "virtues": [
            "First day of the Islamic week.",
            "The Prophet ﷺ and companions set out on journeys on Sundays, considering it a blessed day to begin travel.",
        ],
        "recommended": [
            "Begin new intentions and good deeds.",
        ],
    },
    "Monday": {
        "name_ar": "الإثنين",
        "virtues": [
            "The Prophet Muhammad ﷺ was born on Monday.",
            "The Quran (first revelation) descended on Monday.",
            "The Prophet ﷺ fasted on Mondays, saying: 'It is a day on which I was born and on which revelation was sent to me.' (Muslim)",
            "Deeds are presented to Allah on Monday and Thursday. (Tirmidhi)",
        ],
        "recommended": [
            "Fasting — Sunnah of the Prophet ﷺ.",
            "Recite extra Salawat (blessings) upon the Prophet ﷺ.",
            "Perform good deeds so they are presented in a state of fasting.",
        ],
    },
    "Tuesday": {
        "name_ar": "الثلاثاء",
        "virtues": [
            "No specific virtue narrated in major hadith, but all days are opportunities for worship.",
        ],
        "recommended": [
            "Maintain regular dhikr, Quran recitation, and voluntary prayers.",
        ],
    },
    "Wednesday": {
        "name_ar": "الأربعاء",
        "virtues": [
            "The Prophet Ayyub ﷺ was cured of his illness on Wednesday.",
            "Ibn Mas'ud reported that the Prophet ﷺ's du'aa was answered on a Wednesday between Dhuhr and Asr. (Ahmad — some scholars grade it hasan)",
        ],
        "recommended": [
            "Make du'aa between Dhuhr and Asr — a recommended time for supplications.",
        ],
    },
    "Thursday": {
        "name_ar": "الخميس",
        "virtues": [
            "Deeds are presented to Allah on Monday and Thursday. (Tirmidhi)",
            "The Prophet ﷺ regularly fasted on Thursdays.",
            "The Prophet ﷺ liked to set out on journeys on Thursday. (Bukhari)",
        ],
        "recommended": [
            "Fasting — Sunnah of the Prophet ﷺ.",
            "Begin important matters and journeys.",
            "Perform good deeds so they are presented in a state of fasting.",
        ],
    },
    "Friday": {
        "name_ar": "الجمعة",
        "virtues": [
            "'The best day on which the sun rises is Friday.' (Muslim)",
            "Adam ﷺ was created on Friday, entered Paradise on Friday, and was taken out of it on Friday.",
            "The Hour (Day of Judgement) will be established on Friday.",
            "There is an hour on Friday during which any du'aa a Muslim makes is answered. (Bukhari, Muslim)",
            "Reading Surah Al-Kahf on Friday gives light between the two Fridays. (Hakim)",
            "Sending abundant Salawat on the Prophet ﷺ is especially rewarded on Friday. (Abu Dawud)",
        ],
        "recommended": [
            "Perform Ghusl (bath) before Jumu'ah prayer.",
            "Jumu'ah (Friday) prayer — obligatory for men.",
            "Recite Surah Al-Kahf.",
            "Send abundant blessings upon the Prophet ﷺ.",
            "Make du'aa — especially in the last hour before Maghrib.",
            "Wear clean clothes and use perfume.",
        ],
    },
    "Saturday": {
        "name_ar": "السبت",
        "virtues": [
            "No specific Islamic virtue narrated. Avoid dedicating it to rest only — use it for worship.",
            "Note: Fasting on Saturday alone (without Friday or Sunday) is disliked unless it is a regular fasting day. (Abu Dawud)",
        ],
        "recommended": [
            "Maintain regular dhikr, Quran recitation, and voluntary prayers.",
        ],
    },
}

HIJRI_MONTHS: Dict[str, tuple] = {
    "muharram":     (1,  "محرم"),
    "safar":        (2,  "صفر"),
    "rabiulawal":   (3,  "ربيع الأول"),
    "rabiulakhir":  (4,  "ربيع الآخر"),
    "jumadalawal":  (5,  "جمادى الأولى"),
    "jumadalakhir": (6,  "جمادى الآخرة"),
    "rajab":        (7,  "رجب"),
    "shaban":       (8,  "شعبان"),
    "ramadan":      (9,  "رمضان"),
    "shawwal":      (10, "شوال"),
    "dhulqada":     (11, "ذو القعدة"),
    "dhulhijja":    (12, "ذو الحجة"),
}


class SkillError(Exception):
    pass


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str

    def to_dict(self) -> Dict[str, str]:
        return {"title": self.title, "link": self.link, "snippet": self.snippet}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    })
    return s


PRIVATE_NETLOCS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}


def validate_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc:
            return False
        host = parsed.hostname or ""
        if host in PRIVATE_NETLOCS:
            return False
        if host.startswith("10.") or host.startswith("192.168."):
            return False
        if re.match(r"^172\.(1[6-9]|2\d|3[0-1])\.", host):
            return False
        return True
    except Exception:
        return False


def normalize_city(city: str) -> str:
    key = city.strip().lower()
    return CITY_ALIASES.get(key, city.strip())


def _method_for_country(country: str) -> int:
    return COUNTRY_METHOD.get(country.strip().lower(), 3)


def _geocode(city: str, country: str) -> tuple:
    """Return (lat, lng) for a city using Nominatim. Raises SkillError on failure."""
    cache_key = f"{city.lower()}|{country.lower()}"
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]
    params = {
        "q": f"{city}, {country}",
        "format": "json",
        "limit": 1,
        "accept-language": "en",
    }
    r = _session().get(NOMINATIM_BASE, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    results = r.json()
    if not results:
        raise SkillError(f"Location not found: '{city}, {country}'. Try a different city name.")
    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])
    _geocode_cache[cache_key] = (lat, lng)
    return lat, lng


def request_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = _session().get(url, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    code = data.get("code", 200)
    if code != 200:
        raise SkillError(data.get("data") or data.get("status") or f"API error {code}")
    return data


def timings_by_city(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    """Fetch prayer timings using accurate coordinates from Nominatim geocoding.

    Uses /timings/{date}?latitude=&longitude= instead of /timingsByCity because
    the timingsByCity endpoint has known geocoding errors (e.g. Damascus returns
    coordinates in West Africa instead of Syria).
    """
    city = normalize_city(city)
    country = country.strip()
    date = date or dt.date.today().strftime("%d-%m-%Y")
    lat, lng = _geocode(city, country)
    method = _method_for_country(country)
    url = f"{ALADHAN_BASE}/timings/{date}"
    params = {"latitude": lat, "longitude": lng, "method": method, "school": 0}
    return request_json(url, params=params)


def gregorian_to_hijri(date_str: str) -> Dict[str, Any]:
    url = f"{ALADHAN_BASE}/gToH/{date_str}"
    return request_json(url)


def hijri_to_gregorian(day: int, month: int, year: int) -> Dict[str, Any]:
    url = f"{ALADHAN_BASE}/hToG/{day:02d}-{month:02d}-{year}"
    return request_json(url)


def _has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def search_web(query: str, max_results: int = 5, site: Optional[str] = None) -> List[SearchResult]:
    """Search via Google News RSS. Reliable, no scraping blocks, returns real article URLs."""
    q = query if not site else f"site:{site} {query}"
    # Use Arabic locale when query contains Arabic text
    if _has_arabic(q):
        params = "hl=ar&gl=SA&ceid=SA:ar"
    else:
        params = "hl=en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&{params}"
    try:
        response = _session().get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SkillError(f"Search failed: {exc}") from exc
    soup = BeautifulSoup(response.text, "xml")
    results: List[SearchResult] = []
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        link_tag = item.find("link")
        source_tag = item.find("source")
        pub_tag = item.find("pubDate")
        if not title_tag or not link_tag:
            continue
        link = (link_tag.text or "").strip()
        if not validate_url(link):
            continue
        title = (title_tag.text or "").strip()
        source = (source_tag.text or "").strip() if source_tag else ""
        pub = (pub_tag.text or "")[:16].strip() if pub_tag else ""
        snippet = f"{source} — {pub}" if source else pub
        results.append(SearchResult(title=title, link=link, snippet=snippet))
        if len(results) >= max_results:
            break
    return results


def read_webpage(url: str, max_chars: int = 10000) -> str:
    if not validate_url(url):
        raise SkillError("Invalid or restricted URL")
    r = _session().get(url, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text[:max_chars]


def _extract_dates_from_text(text: str) -> List[dt.date]:
    """
    Find all Gregorian date mentions in Arabic or English text.
    Patterns matched: "20 March 2026", "March 20, 2026", "20 مارس 2026".
    """
    found: List[dt.date] = []
    months_en_pat = "|".join(re.escape(k) for k in GREG_MONTHS_EN)
    months_ar_pat = "|".join(re.escape(k) for k in GREG_MONTHS_AR)

    # English: "20 March 2026" or "March 20, 2026"
    for m in re.finditer(rf"\b(\d{{1,2}})\s+({months_en_pat})\s+(\d{{4}})\b", text, re.IGNORECASE):
        try:
            found.append(dt.date(int(m.group(3)), GREG_MONTHS_EN[m.group(2).lower()], int(m.group(1))))
        except ValueError:
            pass
    for m in re.finditer(rf"\b({months_en_pat})\s+(\d{{1,2}})[,\s]+(\d{{4}})\b", text, re.IGNORECASE):
        try:
            found.append(dt.date(int(m.group(3)), GREG_MONTHS_EN[m.group(1).lower()], int(m.group(2))))
        except ValueError:
            pass

    # Arabic: "20 مارس 2026"
    for m in re.finditer(rf"(\d{{1,2}})\s+({months_ar_pat})\s+(\d{{4}})", text):
        try:
            found.append(dt.date(int(m.group(3)), GREG_MONTHS_AR[m.group(2)], int(m.group(1))))
        except ValueError:
            pass

    return found


def _search_announced_start(
    country: str,
    month_ar: str,
    hijri_year: int,
    calc_date: dt.date,
    gregorian_year: int,
    extra_terms: Optional[List[str]] = None,
) -> Optional[Dict[str, str]]:
    """
    Search news for the official hilal announcement and try to extract the
    actual announced start date for a Hijri month in a given country.

    Returns {"announced_date": "DD-MM-YYYY", "source": str, "link": str}
    or None if no reliable date is found within ±2 days of calc_date.
    """
    window = 2  # days
    terms = [
        f"رؤية هلال {month_ar} {hijri_year} {country}",
        f"إعلان بداية {month_ar} {hijri_year} {country}",
        f"hilal {month_ar} moon sighting {gregorian_year} {country}",
    ]
    if extra_terms:
        terms = extra_terms + terms

    # Collect search results
    seen: set = set()
    results: List[SearchResult] = []
    for term in terms:
        for item in search_web(term, max_results=4):
            if item.link not in seen:
                seen.add(item.link)
                results.append(item)
        if len(results) >= 8:
            break

    def _closest(dates: List[dt.date]) -> Optional[dt.date]:
        """Return the date closest to calc_date within the window, or None."""
        candidates = [d for d in dates if abs((d - calc_date).days) <= window]
        if not candidates:
            return None
        return min(candidates, key=lambda d: abs((d - calc_date).days))

    # 1. Fast pass: check titles + snippets first (no HTTP read needed)
    for item in results:
        dates = _extract_dates_from_text(item.title + " " + item.snippet)
        d = _closest(dates)
        if d:
            return {
                "announced_date": d.strftime("%d-%m-%Y"),
                "source": item.title[:120],
                "link": item.link,
                "method": "news_title",
            }

    # 2. Deep pass: read the top articles
    for item in results[:3]:
        try:
            text = read_webpage(item.link, max_chars=4000)
            dates = _extract_dates_from_text(text)
            d = _closest(dates)
            if d:
                return {
                    "announced_date": d.strftime("%d-%m-%Y"),
                    "source": item.title[:120],
                    "link": item.link,
                    "method": "article_text",
                }
        except Exception:
            continue

    return None


def _extract_time(value: str) -> str:
    """Strip timezone suffix like '(AST)' from 'HH:MM (AST)' → 'HH:MM'."""
    return re.sub(r"\s*\([^)]+\)", "", value or "").strip()


def _parse_hhmm(value: str) -> dt.datetime:
    return dt.datetime.strptime(_extract_time(value), "%H:%M")


def get_prayer_summary(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    payload = timings_by_city(city=city, country=country, date=date)
    timings = payload["data"]["timings"]
    date_info = payload["data"]["date"]
    weekday_en = date_info["gregorian"]["weekday"]["en"]
    weekday_ar = date_info["hijri"].get("weekday", {}).get("ar", "")
    return {
        "city": normalize_city(city),
        "country": country,
        "gregorian": date_info["gregorian"]["date"],
        "hijri": date_info["hijri"]["date"],
        "weekday_en": weekday_en,
        "weekday_ar": weekday_ar,
        "fajr": _extract_time(timings.get("Fajr", "")),
        "sunrise": _extract_time(timings.get("Sunrise", "")),
        "dhuhr": _extract_time(timings.get("Dhuhr", "")),
        "asr": _extract_time(timings.get("Asr", "")),
        "maghrib": _extract_time(timings.get("Maghrib", "")),
        "isha": _extract_time(timings.get("Isha", "")),
        "midnight": _extract_time(timings.get("Midnight", "")),
        "method": payload["data"]["meta"].get("method", {}).get("name", "Unknown"),
        "timezone": payload["data"]["meta"].get("timezone"),
    }


def get_day_info(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    """Return Islamic history/virtues for the day + prayer times for that city."""
    prayer = get_prayer_summary(city=city, country=country, date=date)
    day = prayer["weekday_en"]
    info = DAY_INFO.get(day, {})
    return {
        "city": prayer["city"],
        "country": prayer["country"],
        "gregorian": prayer["gregorian"],
        "hijri": prayer["hijri"],
        "weekday_en": day,
        "weekday_ar": prayer.get("weekday_ar", ""),
        "virtues": info.get("virtues", []),
        "recommended_acts": info.get("recommended", []),
        "prayer_times": {
            "fajr": prayer["fajr"],
            "sunrise": prayer["sunrise"],
            "dhuhr": prayer["dhuhr"],
            "asr": prayer["asr"],
            "maghrib": prayer["maghrib"],
            "isha": prayer["isha"],
        },
    }


def get_qiyam_time(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    """Calculate Qiyam al-Layl time: the last third of the night (Maghrib → Fajr)."""
    today_str = date or dt.date.today().strftime("%d-%m-%Y")
    today_date = dt.datetime.strptime(today_str, "%d-%m-%Y").date()
    tomorrow_str = (today_date + dt.timedelta(days=1)).strftime("%d-%m-%Y")

    today_payload = timings_by_city(city=city, country=country, date=today_str)
    tomorrow_payload = timings_by_city(city=city, country=country, date=tomorrow_str)

    today_timings = today_payload["data"]["timings"]
    tomorrow_timings = tomorrow_payload["data"]["timings"]

    maghrib_str = _extract_time(today_timings.get("Maghrib", ""))
    isha_str = _extract_time(today_timings.get("Isha", ""))
    fajr_next_str = _extract_time(tomorrow_timings.get("Fajr", ""))

    # Night = Maghrib (day 1) → Fajr (day 2)
    maghrib_dt = _parse_hhmm(maghrib_str).replace(year=2000, month=1, day=1)
    fajr_dt = _parse_hhmm(fajr_next_str).replace(year=2000, month=1, day=2)
    night = fajr_dt - maghrib_dt
    third = night / 3

    qiyam_start = maghrib_dt + 2 * third
    secs = int(night.total_seconds())

    return {
        "city": normalize_city(city),
        "country": country,
        "date": today_str,
        "maghrib": maghrib_str,
        "isha": isha_str,
        "fajr_next_day": fajr_next_str,
        "night_duration": f"{secs // 3600}h {(secs % 3600) // 60}m",
        "last_third_starts": qiyam_start.strftime("%H:%M"),
        "last_third_ends_at_fajr": fajr_next_str,
        "note": "Qiyam al-Layl is best from last_third_starts until Fajr the next morning.",
    }


def hilal_sighting(country: str, month: str = "ramadan", year: Optional[int] = None) -> Dict[str, Any]:
    """
    Look up moon (hilal) sighting news and calculate the expected start of a Hijri month.

    The calculated start uses the AlAdhan Umm al-Qura calculation. Actual sighting
    in a given country may be announced one day earlier or later depending on local
    astronomical committees and official announcements.
    """
    year = year or dt.date.today().year
    key = month.lower().replace(" ", "").replace("-", "").replace("_", "")
    if key not in HIJRI_MONTHS:
        raise SkillError(f"Unknown Hijri month '{month}'. Valid keys: {', '.join(HIJRI_MONTHS)}")

    month_num, month_ar = HIJRI_MONTHS[key]

    # Determine which Hijri year corresponds to this Gregorian year
    hijri_payload = gregorian_to_hijri(dt.date(year, 1, 1).strftime("%d-%m-%Y"))
    hijri_year = int(hijri_payload["data"]["hijri"]["year"])

    # Calculated 1st of the target month (Umm al-Qura)
    g_start = hijri_to_gregorian(1, month_num, hijri_year)
    start_gregorian = g_start["data"]["gregorian"]["date"]

    # Eve = 29th of the previous month (when hilal would be looked for)
    prev_month = 12 if month_num == 1 else month_num - 1
    prev_hijri_year = hijri_year - 1 if month_num == 1 else hijri_year
    g_eve = hijri_to_gregorian(29, prev_month, prev_hijri_year)
    eve_gregorian = g_eve["data"]["gregorian"]["date"]

    calc_date = dt.datetime.strptime(start_gregorian, "%d-%m-%Y").date()

    # Try to find the officially announced start date from news
    announcement = _search_announced_start(
        country=country,
        month_ar=month_ar,
        hijri_year=hijri_year,
        calc_date=calc_date,
        gregorian_year=year,
    )
    announced_start = announcement["announced_date"] if announcement else None
    date_used = announced_start or start_gregorian
    date_status = "announced" if announced_start else "calculated (Umm al-Qura — unconfirmed)"

    # Collect supporting news links
    extra_terms = [
        f"رؤية هلال {month_ar} {hijri_year} {country}",
        f"إعلان رؤية هلال {month_ar} {country} {year}",
        f"hilal moon sighting {key} {year} {country}",
    ]
    news: List[Dict[str, str]] = []
    seen: set = set()
    for term in extra_terms:
        for item in search_web(term, max_results=4):
            if item.link in seen:
                continue
            seen.add(item.link)
            news.append(item.to_dict())
            if len(news) >= 6:
                break
        if len(news) >= 6:
            break

    result: Dict[str, Any] = {
        "country": country,
        "month": key,
        "month_ar": month_ar,
        "hijri_year": hijri_year,
        "calculated_start_gregorian": start_gregorian,
        "hilal_eve_gregorian": eve_gregorian,
        "announced_start_gregorian": announced_start,
        "date_used": date_used,
        "date_status": date_status,
        "moon_sighting_news": news,
    }
    if announcement:
        result["announcement_source"] = announcement["source"]
        result["announcement_link"] = announcement["link"]
    return result


def _hijri_year_for(gregorian_year: int, hijri_month: int) -> int:
    """
    Return the Hijri year whose given month (1-12) falls inside `gregorian_year`.
    Tries the Hijri year derived from Jan 1 first; if the resulting Gregorian date
    lands outside the target year it retries with hijri_year ± 1.
    """
    base_payload = gregorian_to_hijri(dt.date(gregorian_year, 1, 1).strftime("%d-%m-%Y"))
    hijri_year = int(base_payload["data"]["hijri"]["year"])
    for candidate in (hijri_year, hijri_year - 1, hijri_year + 1):
        g = hijri_to_gregorian(1, hijri_month, candidate)
        g_year = int(g["data"]["gregorian"]["date"].split("-")[2])
        if g_year == gregorian_year:
            return candidate
    # Fallback: return the base estimate
    return hijri_year


def estimate_eid_prayer(city: str, country: str = "Saudi Arabia", year: Optional[int] = None, eid: str = "fitr") -> Dict[str, Any]:
    year = year or dt.date.today().year
    if eid not in {"fitr", "adha"}:
        raise SkillError("eid must be 'fitr' or 'adha'")

    target_day = 1 if eid == "fitr" else 10
    hilal_month = 10 if eid == "fitr" else 12          # month whose hilal starts the countdown
    _, month_ar = HIJRI_MONTHS["shawwal" if eid == "fitr" else "dhulhijja"]
    hijri_year = _hijri_year_for(year, hilal_month)
    g = hijri_to_gregorian(target_day, hilal_month, hijri_year)
    calc_date_str = g["data"]["gregorian"]["date"]
    calc_date = dt.datetime.strptime(calc_date_str, "%d-%m-%Y").date()

    # Search for the officially announced date for this country
    extra_terms = [
        f"{'عيد الفطر' if eid == 'fitr' else 'عيد الأضحى'} {country} {year} موعد",
        f"Eid {'Fitr' if eid == 'fitr' else 'Adha'} {year} {country} date announced",
    ]
    announcement = _search_announced_start(
        country=country,
        month_ar=month_ar,
        hijri_year=hijri_year,
        calc_date=calc_date,
        gregorian_year=year,
        extra_terms=extra_terms,
    )
    announced_date_str = announcement["announced_date"] if announcement else None
    date_used_str = announced_date_str or calc_date_str
    date_status = "announced" if announced_date_str else "calculated (Umm al-Qura — unconfirmed)"

    # Get prayer times for the date actually used
    prayer = get_prayer_summary(city, country=country, date=date_used_str)
    sunrise = _parse_hhmm(prayer["sunrise"])
    estimated_prayer = (sunrise + dt.timedelta(minutes=15)).strftime("%H:%M")

    # News links for local prayer time confirmation
    news_terms = [
        f"صلاة عيد {'الفطر' if eid == 'fitr' else 'الأضحى'} {normalize_city(city)} {country} {year}",
        f"Eid {'Fitr' if eid == 'fitr' else 'Adha'} prayer time {normalize_city(city)} {country} {year}",
    ]
    news: List[Dict[str, str]] = []
    seen: set = set()
    for term in news_terms:
        for item in search_web(term, max_results=4):
            if item.link in seen:
                continue
            seen.add(item.link)
            news.append(item.to_dict())
            if len(news) >= 5:
                break
        if len(news) >= 5:
            break

    result: Dict[str, Any] = {
        "city": normalize_city(city),
        "country": country,
        "eid": "Eid al-Fitr" if eid == "fitr" else "Eid al-Adha",
        "calculated_date": calc_date_str,
        "announced_date": announced_date_str,
        "date_used": date_used_str,
        "date_status": date_status,
        "estimated_prayer_time": estimated_prayer,
        "prayer_basis": "Sunrise + 15 min on date_used. Verify with local mosque.",
        "supporting_news_results": news,
    }
    if announcement:
        result["announcement_source"] = announcement["source"]
        result["announcement_link"] = announcement["link"]
    # Keep legacy field so next_eid / next_islamic_events still work
    result["estimated_date"] = date_used_str
    return result


def get_arafah_day(city: str, country: str = "Saudi Arabia", year: Optional[int] = None) -> Dict[str, Any]:
    """
    Return Yawm Arafah (9th Dhul Hijjah) date and prayer times.

    Arafah is the day before Eid al-Adha and follows Saudi Arabia's official
    Dhul Hijjah announcement (Hajj is always in Mecca). We search for the
    announced start of Dhul Hijjah in Saudi Arabia and derive Arafah from that.
    """
    year = year or dt.date.today().year
    hijri_year = _hijri_year_for(year, 12)
    _, dhulhijja_ar = HIJRI_MONTHS["dhulhijja"]

    # Calculated dates
    calc_arafah_str = hijri_to_gregorian(9, 12, hijri_year)["data"]["gregorian"]["date"]
    calc_adha_str   = hijri_to_gregorian(10, 12, hijri_year)["data"]["gregorian"]["date"]
    calc_arafah = dt.datetime.strptime(calc_arafah_str, "%d-%m-%Y").date()

    # Arafah always follows Saudi Arabia's Dhul Hijjah sighting (Hajj is there)
    # Search using Saudi Arabia regardless of the city's country
    announcement = _search_announced_start(
        country="Saudi Arabia",
        month_ar=dhulhijja_ar,
        hijri_year=hijri_year,
        calc_date=calc_arafah,          # Arafah = 9 DH ≈ calc date
        gregorian_year=year,
        extra_terms=[
            f"Eid al-Adha {year} Saudi Arabia date announced",
            f"عيد الأضحى {year} السعودية موعد",
            f"يوم عرفة {hijri_year} السعودية",
        ],
    )

    if announcement:
        # If the found date matches Eid al-Adha calc ± 2, treat it as Eid; Arafah = Eid − 1
        found = dt.datetime.strptime(announcement["announced_date"], "%d-%m-%Y").date()
        calc_adha = dt.datetime.strptime(calc_adha_str, "%d-%m-%Y").date()
        if abs((found - calc_adha).days) <= 2:
            announced_adha = found
            announced_arafah = (found - dt.timedelta(days=1)).strftime("%d-%m-%Y")
        else:
            # Found date is Arafah itself
            announced_arafah = announcement["announced_date"]
            announced_adha = (found + dt.timedelta(days=1))
            announced_adha = announced_adha.strftime("%d-%m-%Y")
        date_used_str = announced_arafah
        date_status = "announced (Saudi Arabia)"
    else:
        date_used_str = calc_arafah_str
        date_status = "calculated (Umm al-Qura — unconfirmed)"
        announced_arafah = None

    prayer = get_prayer_summary(city, country=country, date=date_used_str)
    result: Dict[str, Any] = {
        "city": normalize_city(city),
        "country": country,
        "event": "Yawm Arafah (Day of Arafah)",
        "hijri_date": f"9 Dhul Hijjah {hijri_year}H",
        "calculated_date": calc_arafah_str,
        "announced_date": announced_arafah,
        "date_used": date_used_str,
        "date_status": date_status,
        "weekday_en": prayer["weekday_en"],
        "weekday_ar": prayer.get("weekday_ar", ""),
        "fasting_virtue": (
            "Fasting on the Day of Arafah expiates the sins of the previous year "
            "and the coming year. (Muslim 1162) — for those not performing Hajj."
        ),
        "note": "Arafah date follows Saudi Arabia's official Dhul Hijjah announcement. "
                "For pilgrims on Hajj, fasting on Arafah is not recommended.",
        "prayer_times": {
            "fajr": prayer["fajr"],
            "sunrise": prayer["sunrise"],
            "dhuhr": prayer["dhuhr"],
            "asr": prayer["asr"],
            "maghrib": prayer["maghrib"],
            "isha": prayer["isha"],
        },
    }
    if announcement:
        result["announcement_source"] = announcement["source"]
        result["announcement_link"] = announcement["link"]
    return result


def get_ashura_day(city: str, country: str = "Saudi Arabia", year: Optional[int] = None) -> Dict[str, Any]:
    """
    Return Yawm Ashura (10th Muharram) date and prayer times.

    Ashura follows the country's own Muharram hilal announcement (unlike Arafah
    which always follows Saudi Arabia). We search for the announced start of
    Muharram 1 in the given country and derive Ashura = Muharram 1 + 9 days.
    """
    year = year or dt.date.today().year
    hijri_year = _hijri_year_for(year, 1)  # Muharram is month 1
    _, muharram_ar = HIJRI_MONTHS["muharram"]

    # Calculated dates
    calc_muharram1_str = hijri_to_gregorian(1, 1, hijri_year)["data"]["gregorian"]["date"]
    calc_ashura_str    = hijri_to_gregorian(10, 1, hijri_year)["data"]["gregorian"]["date"]
    calc_tasua_str     = hijri_to_gregorian(9, 1, hijri_year)["data"]["gregorian"]["date"]
    calc_muharram1 = dt.datetime.strptime(calc_muharram1_str, "%d-%m-%Y").date()

    # Search for the announced start of Muharram in the given country
    announcement = _search_announced_start(
        country=country,
        month_ar=muharram_ar,
        hijri_year=hijri_year,
        calc_date=calc_muharram1,
        gregorian_year=year,
        extra_terms=[
            f"رؤية هلال محرم {hijri_year} {country}",
            f"Muharram {year} {country} moon sighting date",
            f"Ashura {year} {country} date",
        ],
    )

    if announcement:
        found = dt.datetime.strptime(announcement["announced_date"], "%d-%m-%Y").date()
        # Derive Ashura and Tasu'a from the announced Muharram 1
        announced_ashura = (found + dt.timedelta(days=9)).strftime("%d-%m-%Y")
        announced_tasua  = (found + dt.timedelta(days=8)).strftime("%d-%m-%Y")
        date_used_str = announced_ashura
        date_status = f"announced ({country})"
    else:
        announced_ashura = None
        announced_tasua  = None
        date_used_str = calc_ashura_str
        date_status = "calculated (Umm al-Qura — unconfirmed)"

    prayer = get_prayer_summary(city, country=country, date=date_used_str)
    result: Dict[str, Any] = {
        "city": normalize_city(city),
        "country": country,
        "event": "Yawm Ashura (Day of Ashura)",
        "hijri_date": f"10 Muharram {hijri_year}H",
        "calculated_date": calc_ashura_str,
        "calculated_tasua": calc_tasua_str,
        "announced_date": announced_ashura,
        "announced_tasua": announced_tasua,
        "date_used": date_used_str,
        "date_status": date_status,
        "weekday_en": prayer["weekday_en"],
        "weekday_ar": prayer.get("weekday_ar", ""),
        "fasting_virtue": (
            "Fasting on the Day of Ashura expiates the sins of the previous year. "
            "(Muslim 1162)"
        ),
        "tasua_note": (
            "The Prophet \ufdfa intended to fast on the 9th (Tasu'a) as well to differ "
            "from the Jewish practice of fasting only on the 10th. (Muslim 1134) — "
            "Fasting both the 9th and 10th is recommended."
        ),
        "note": (
            "Ashura date follows the official Muharram hilal announcement for the given country."
        ),
        "prayer_times": {
            "fajr": prayer["fajr"],
            "sunrise": prayer["sunrise"],
            "dhuhr": prayer["dhuhr"],
            "asr": prayer["asr"],
            "maghrib": prayer["maghrib"],
            "isha": prayer["isha"],
        },
    }
    if announcement:
        result["announcement_source"] = announcement["source"]
        result["announcement_link"] = announcement["link"]
    return result


def next_eid(city: str, country: str = "Saudi Arabia") -> Dict[str, Any]:
    today = dt.date.today()
    for year in (today.year, today.year + 1):
        candidates = [
            estimate_eid_prayer(city, country=country, year=year, eid="fitr"),
            estimate_eid_prayer(city, country=country, year=year, eid="adha"),
        ]
        for item in candidates:
            d = dt.datetime.strptime(item["estimated_date"], "%d-%m-%Y").date()
            if d >= today:
                result = dict(item)
                result["days_until"] = (d - today).days
                return result
    # Should never reach here, but return first candidate as fallback
    result = dict(candidates[0])
    result["days_until"] = None
    return result


def next_islamic_events(city: str, country: str = "Saudi Arabia") -> List[Dict[str, Any]]:
    """Return all three upcoming major events — Yawm Arafah, Eid al-Fitr, Eid al-Adha — sorted by date."""
    today = dt.date.today()
    events: List[tuple] = []
    for year in (today.year, today.year + 1):
        for eid in ("fitr", "adha"):
            item = estimate_eid_prayer(city, country=country, year=year, eid=eid)
            d = dt.datetime.strptime(item["estimated_date"], "%d-%m-%Y").date()
            if d >= today:
                events.append((d, {
                    "event": item["eid"],
                    "gregorian_date": item["estimated_date"],
                    "estimated_prayer_time": item["estimated_prayer_time"],
                    "days_until": (d - today).days,
                    "city": item["city"],
                    "country": item["country"],
                }))
        arafah = get_arafah_day(city, country=country, year=year)
        d = dt.datetime.strptime(arafah["date_used"], "%d-%m-%Y").date()
        if d >= today:
            events.append((d, {
                "event": arafah["event"],
                "gregorian_date": arafah["date_used"],
                "hijri_date": arafah["hijri_date"],
                "fasting_virtue": arafah["fasting_virtue"],
                "days_until": (d - today).days,
                "city": arafah["city"],
                "country": arafah["country"],
            }))

    events.sort(key=lambda x: x[0])
    # Return the first 3 distinct upcoming events
    seen_events: set = set()
    result = []
    for _, item in events:
        if item["event"] not in seen_events:
            seen_events.add(item["event"])
            result.append(item)
        if len(result) == 3:
            break
    return result


def format_hijri_conversion(date_str: Optional[str] = None, day: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
    if date_str:
        payload = gregorian_to_hijri(date_str)
        d = payload["data"]
        return {
            "mode": "gregorian_to_hijri",
            "gregorian": d["gregorian"]["date"],
            "hijri": d["hijri"]["date"],
            "hijri_month_en": d["hijri"]["month"]["en"],
            "hijri_month_ar": d["hijri"]["month"].get("ar"),
            "weekday_en": d["gregorian"]["weekday"]["en"],
        }
    if day is None or month is None or year is None:
        raise SkillError("Provide either --date DD-MM-YYYY or --day --month --year")
    payload = hijri_to_gregorian(day, month, year)
    d = payload["data"]
    return {
        "mode": "hijri_to_gregorian",
        "hijri": d["hijri"]["date"],
        "gregorian": d["gregorian"]["date"],
        "gregorian_month_en": d["gregorian"]["month"]["en"],
        "weekday_en": d["gregorian"]["weekday"]["en"],
    }


def print_json(data: Any) -> None:
    out = json.dumps(data, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


def cmd_prayer(args: argparse.Namespace) -> None:
    print_json(get_prayer_summary(city=args.city, country=args.country, date=args.date))


def cmd_day_info(args: argparse.Namespace) -> None:
    print_json(get_day_info(city=args.city, country=args.country, date=args.date))


def cmd_qiyam(args: argparse.Namespace) -> None:
    print_json(get_qiyam_time(city=args.city, country=args.country, date=args.date))


def cmd_hijri(args: argparse.Namespace) -> None:
    print_json(format_hijri_conversion(date_str=args.date, day=args.day, month=args.month, year=args.year))


def cmd_next_eid(args: argparse.Namespace) -> None:
    print_json(next_eid(city=args.city, country=args.country))


def cmd_arafah(args: argparse.Namespace) -> None:
    print_json(get_arafah_day(city=args.city, country=args.country, year=args.year))


def cmd_ashura(args: argparse.Namespace) -> None:
    print_json(get_ashura_day(city=args.city, country=args.country, year=args.year))


def cmd_next_events(args: argparse.Namespace) -> None:
    print_json(next_islamic_events(city=args.city, country=args.country))


def cmd_eid_prayer(args: argparse.Namespace) -> None:
    print_json(estimate_eid_prayer(city=args.city, country=args.country, year=args.year, eid=args.eid))


def cmd_hilal(args: argparse.Namespace) -> None:
    print_json(hilal_sighting(country=args.country, month=args.month, year=args.year))


def cmd_news(args: argparse.Namespace) -> None:
    items = [item.to_dict() for item in search_web(query=args.query, max_results=args.max_results, site=args.site)]
    print_json(items)


def cmd_read(args: argparse.Namespace) -> None:
    print(read_webpage(url=args.url, max_chars=args.max_chars))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Global Islamic Faith Utils skill helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prayer = sub.add_parser("prayer", help="Get prayer times for any city worldwide")
    p_prayer.add_argument("--city", default="Riyadh")
    p_prayer.add_argument("--country", default="Saudi Arabia")
    p_prayer.add_argument("--date", help="DD-MM-YYYY")
    p_prayer.set_defaults(func=cmd_prayer)

    p_day = sub.add_parser("day-info", help="Islamic history and virtues of the day + prayer times")
    p_day.add_argument("--city", default="Riyadh")
    p_day.add_argument("--country", default="Saudi Arabia")
    p_day.add_argument("--date", help="DD-MM-YYYY (defaults to today)")
    p_day.set_defaults(func=cmd_day_info)

    p_qiyam = sub.add_parser("qiyam", help="Calculate Qiyam al-Layl (last third of night) for a city")
    p_qiyam.add_argument("--city", default="Riyadh")
    p_qiyam.add_argument("--country", default="Saudi Arabia")
    p_qiyam.add_argument("--date", help="DD-MM-YYYY (defaults to today)")
    p_qiyam.set_defaults(func=cmd_qiyam)

    p_hijri = sub.add_parser("hijri", help="Convert Gregorian↔Hijri")
    p_hijri.add_argument("--date", help="Gregorian DD-MM-YYYY")
    p_hijri.add_argument("--day", type=int)
    p_hijri.add_argument("--month", type=int)
    p_hijri.add_argument("--year", type=int)
    p_hijri.set_defaults(func=cmd_hijri)

    p_next = sub.add_parser("next-eid", help="Get next upcoming Eid (checks next year if current year has passed)")
    p_next.add_argument("--city", default="Riyadh")
    p_next.add_argument("--country", default="Saudi Arabia")
    p_next.set_defaults(func=cmd_next_eid)

    p_arafah = sub.add_parser("arafah", help="Get Yawm Arafah (9th Dhul Hijjah) date and prayer times")
    p_arafah.add_argument("--city", default="Riyadh")
    p_arafah.add_argument("--country", default="Saudi Arabia")
    p_arafah.add_argument("--year", type=int, help="Gregorian year (defaults to current year)")
    p_arafah.set_defaults(func=cmd_arafah)

    p_ashura = sub.add_parser("ashura", help="Get Yawm Ashura (10th Muharram) date, fasting virtue, and prayer times")
    p_ashura.add_argument("--city", default="Riyadh")
    p_ashura.add_argument("--country", default="Saudi Arabia")
    p_ashura.add_argument("--year", type=int, help="Gregorian year (defaults to current year)")
    p_ashura.set_defaults(func=cmd_ashura)

    p_events = sub.add_parser("next-events", help="Next 3 upcoming Islamic events: Yawm Arafah, Eid al-Fitr, Eid al-Adha")
    p_events.add_argument("--city", default="Riyadh")
    p_events.add_argument("--country", default="Saudi Arabia")
    p_events.set_defaults(func=cmd_next_events)

    p_eid = sub.add_parser("eid-prayer", help="Estimate Eid prayer time and fetch web results")
    p_eid.add_argument("--city", default="Riyadh")
    p_eid.add_argument("--country", default="Saudi Arabia")
    p_eid.add_argument("--year", type=int)
    p_eid.add_argument("--eid", choices=["fitr", "adha"], default="fitr")
    p_eid.set_defaults(func=cmd_eid_prayer)

    p_hilal = sub.add_parser("hilal", help="Check hilal moon sighting news and calculated start of a Hijri month")
    p_hilal.add_argument("--country", default="Saudi Arabia")
    p_hilal.add_argument("--month", default="ramadan",
                         help=f"Hijri month key. Valid: {', '.join(HIJRI_MONTHS)}")
    p_hilal.add_argument("--year", type=int, help="Gregorian year (defaults to current year)")
    p_hilal.set_defaults(func=cmd_hilal)

    p_news = sub.add_parser("news", help="Search Google News RSS (Arabic or English auto-detected)")
    p_news.add_argument("query")
    p_news.add_argument("--max-results", type=int, default=5, dest="max_results")
    p_news.add_argument("--site", help="Optional site filter, e.g. spa.gov.sa")
    p_news.set_defaults(func=cmd_news)

    p_read = sub.add_parser("read", help="Read webpage text")
    p_read.add_argument("url")
    p_read.add_argument("--max-chars", type=int, default=6000, dest="max_chars")
    p_read.set_defaults(func=cmd_read)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        return 2
    except SkillError as exc:
        print(f"Skill error: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
