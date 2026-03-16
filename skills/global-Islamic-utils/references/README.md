# Global Islamic Utils — Notes

## Requirements

Install Python packages:

```bash
pip install requests beautifulsoup4
```

## Quick test

```bash
python scripts/islamic_faith_utils.py prayer --city Riyadh
python scripts/islamic_faith_utils.py hijri --date 30-03-2026
python scripts/islamic_faith_utils.py next-eid --city Riyadh
python scripts/islamic_faith_utils.py news "صلاة العيد الرياض" --site spa.gov.sa
```

## Notes

- City aliases support Arabic and English for common cities (e.g. "الرياض" → Riyadh).
- Coordinates are resolved via Nominatim (OpenStreetMap) for accuracy — the AlAdhan city endpoint has known geocoding bugs (e.g. Damascus resolves to West Africa).
- Prayer calculation method is selected per country (Umm al-Qura for Saudi Arabia, ISNA for USA/Canada, etc.).
- Eid prayer time is estimated (Sunrise + 15 min) — always verify with the local mosque.
- Hilal announcement search uses Google News RSS and may not always find the official announcement.
- For authoritative Saudi announcements, try `--site spa.gov.sa`.

## Examples

```bash
python scripts/islamic_faith_utils.py prayer --city London --country "United Kingdom"
python scripts/islamic_faith_utils.py eid-prayer --city Tokyo --country Japan --eid fitr
python scripts/islamic_faith_utils.py next-events --city "Kuala Lumpur" --country Malaysia
python scripts/islamic_faith_utils.py arafah --city Jakarta --country Indonesia --year 2026
```
