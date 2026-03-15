#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
ALADHAN_BASE = "https://api.aladhan.com/v1"
CITY_ALIASES = {
    # Arabic aliases kept for convenience; all other cities worldwide are accepted as-is.
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
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _clean_url(url: str) -> str:
    # DuckDuckGo HTML sometimes returns protocol-relative links or redirect URLs.
    url = (url or "").strip()
    if url.startswith("//"):
        url = "https:" + url
    return url


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


def request_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    r = _session().get(url, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    code = data.get("code", 200)
    if code != 200:
        raise SkillError(data.get("data") or data.get("status") or f"API error {code}")
    return data


def timings_by_city(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    city = normalize_city(city)
    country = country.strip()
    date = date or dt.date.today().strftime("%d-%m-%Y")
    url = f"{ALADHAN_BASE}/timingsByCity/{date}"
    params = {"city": city, "country": country, "method": 4, "school": 1, "iso8601": True}
    return request_json(url, params=params)


# Umm al-Qura / Saudi-relevant calendar conversion via AlAdhan.
def gregorian_to_hijri(date_str: str) -> Dict[str, Any]:
    url = f"{ALADHAN_BASE}/gToH/{date_str}"
    return request_json(url)


def hijri_to_gregorian(day: int, month: int, year: int) -> Dict[str, Any]:
    url = f"{ALADHAN_BASE}/hToG/{day:02d}-{month:02d}-{year}"
    return request_json(url)


def search_web(query: str, max_results: int = 5, site: Optional[str] = None) -> List[SearchResult]:
    q = query if not site else f"site:{site} {query}"
    url = "https://html.duckduckgo.com/html/"
    response = _session().post(url, data={"q": q}, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: List[SearchResult] = []
    for result in soup.find_all("div", class_="result", limit=max_results):
        title_tag = result.find("a", class_="result__a")
        snippet_tag = result.find("a", class_="result__snippet")
        if not title_tag:
            continue
        link = _clean_url(title_tag.get("href", ""))
        if not validate_url(link):
            continue
        title = title_tag.get_text(" ", strip=True)
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
        results.append(SearchResult(title=title, link=link, snippet=snippet))
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


def _extract_time(value: str) -> str:
    return re.sub(r"\s*\([^)]+\)", "", value or "").strip()


def get_prayer_summary(city: str, country: str = "Saudi Arabia", date: Optional[str] = None) -> Dict[str, Any]:
    payload = timings_by_city(city=city, country=country, date=date)
    timings = payload["data"]["timings"]
    date_info = payload["data"]["date"]
    return {
        "city": normalize_city(city),
        "country": country,
        "country": country,
        "gregorian": date_info["gregorian"]["date"],
        "hijri": date_info["hijri"]["date"],
        "weekday_en": date_info["gregorian"]["weekday"]["en"],
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


def estimate_eid_prayer(city: str, country: str = "Saudi Arabia", year: Optional[int] = None, eid: str = "fitr") -> Dict[str, Any]:
    year = year or dt.date.today().year
    if eid not in {"fitr", "adha"}:
        raise SkillError("eid must be 'fitr' or 'adha'")

    # Saudi calendar defaults: 1 Shawwal for Eid al-Fitr, 10 Dhu al-Hijjah for Eid al-Adha.
    hijri_payload = gregorian_to_hijri(dt.date(year, 1, 1).strftime("%d-%m-%Y"))
    hijri_year = int(hijri_payload["data"]["hijri"]["year"])
    target_day = 1 if eid == "fitr" else 10
    target_month = 10 if eid == "fitr" else 12
    g = hijri_to_gregorian(target_day, target_month, hijri_year)
    g_date = g["data"]["gregorian"]["date"]

    prayer = get_prayer_summary(city, country=country, date=g_date)
    sunrise = dt.datetime.strptime(prayer["sunrise"], "%H:%M")
    estimated = (sunrise + dt.timedelta(minutes=15)).strftime("%H:%M")

    search_terms = [
        f"صلاة عيد {'الفطر' if eid == 'fitr' else 'الأضحى'} {normalize_city(city)} {country} {year}",
        f"Eid {'Fitr' if eid == 'fitr' else 'Adha'} prayer time {normalize_city(city)} {country} {year}",
    ]
    news: List[Dict[str, str]] = []
    seen = set()
    for term in search_terms:
        for item in search_web(term, max_results=4):
            if item.link in seen:
                continue
            seen.add(item.link)
            news.append(item.to_dict())
            if len(news) >= 5:
                break
        if len(news) >= 5:
            break

    return {
        "city": normalize_city(city),
        "country": country,
        "eid": "Eid al-Fitr" if eid == "fitr" else "Eid al-Adha",
        "estimated_date": g_date,
        "estimated_prayer_time": estimated,
        "basis": "Estimated as Sunrise + 15 minutes. Verify with your local mosque or official local announcement.",
        "supporting_news_results": news,
    }


def next_eid(city: str, country: str = "Saudi Arabia") -> Dict[str, Any]:
    today = dt.date.today()
    current_year = today.year
    candidates = [
        estimate_eid_prayer(city, country=country, year=current_year, eid="fitr"),
        estimate_eid_prayer(city, country=country, year=current_year, eid="adha"),
    ]
    parsed = []
    for item in candidates:
        d = dt.datetime.strptime(item["estimated_date"], "%d-%m-%Y").date()
        parsed.append((d, item))
    future = [item for item in parsed if item[0] >= today]
    chosen = future[0] if future else min(parsed, key=lambda x: x[0])
    result = dict(chosen[1])
    result["days_until"] = (chosen[0] - today).days if chosen[0] >= today else None
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


def print_json(data: Dict[str, Any] | List[Dict[str, Any]]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_prayer(args: argparse.Namespace) -> None:
    print_json(get_prayer_summary(city=args.city, country=args.country, date=args.date))


def cmd_hijri(args: argparse.Namespace) -> None:
    print_json(format_hijri_conversion(date_str=args.date, day=args.day, month=args.month, year=args.year))


def cmd_next_eid(args: argparse.Namespace) -> None:
    print_json(next_eid(city=args.city, country=args.country))


def cmd_eid_prayer(args: argparse.Namespace) -> None:
    print_json(estimate_eid_prayer(city=args.city, country=args.country, year=args.year, eid=args.eid))


def cmd_news(args: argparse.Namespace) -> None:
    items = [item.to_dict() for item in search_web(query=args.query, max_results=args.max_results, site=args.site)]
    print_json(items)


def cmd_read(args: argparse.Namespace) -> None:
    print(read_webpage(url=args.url, max_chars=args.max_chars))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Global Faith Utils skill helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prayer = sub.add_parser("prayer", help="Get prayer times for any city worldwide")
    p_prayer.add_argument("--city", default="Riyadh")
    p_prayer.add_argument("--country", default="Saudi Arabia")
    p_prayer.add_argument("--date", help="DD-MM-YYYY")
    p_prayer.set_defaults(func=cmd_prayer)

    p_hijri = sub.add_parser("hijri", help="Convert Gregorian↔Hijri")
    p_hijri.add_argument("--date", help="Gregorian DD-MM-YYYY")
    p_hijri.add_argument("--day", type=int)
    p_hijri.add_argument("--month", type=int)
    p_hijri.add_argument("--year", type=int)
    p_hijri.set_defaults(func=cmd_hijri)

    p_next = sub.add_parser("next-eid", help="Get next Eid estimate and local news links")
    p_next.add_argument("--city", default="Riyadh")
    p_next.add_argument("--country", default="Saudi Arabia")
    p_next.set_defaults(func=cmd_next_eid)

    p_eid = sub.add_parser("eid-prayer", help="Estimate Eid prayer time and fetch web results")
    p_eid.add_argument("--city", default="Riyadh")
    p_eid.add_argument("--country", default="Saudi Arabia")
    p_eid.add_argument("--year", type=int)
    p_eid.add_argument("--eid", choices=["fitr", "adha"], default="fitr")
    p_eid.set_defaults(func=cmd_eid_prayer)

    p_news = sub.add_parser("news", help="Search news/web via DuckDuckGo HTML")
    p_news.add_argument("query")
    p_news.add_argument("--max-results", type=int, default=5)
    p_news.add_argument("--site", help="Optional site filter, e.g. spa.gov.sa")
    p_news.set_defaults(func=cmd_news)

    p_read = sub.add_parser("read", help="Read webpage text")
    p_read.add_argument("url")
    p_read.add_argument("--max-chars", type=int, default=6000)
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
