# KSA Faith Utils — Notes

## Requirements

Install Python packages:

```bash
pip install requests beautifulsoup4
```

## Suggested workspace location

```bash
mkdir -p skills
cp -r openclaw-ksa-faith-utils skills/ksa-faith-utils
```

## Quick test

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py prayer --city Riyadh
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py hijri --date 30-03-2026
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py next-eid --city Riyadh
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py news "صلاة العيد الرياض" --site spa.gov.sa
```

## Notes about local Saudi behavior

- City aliases support Arabic and English for common Saudi cities.
- Eid prayer is estimated, not officially guaranteed.
- Search results come from DuckDuckGo HTML and may vary.
- For public guidance, always prefer official Saudi sources.


Examples:
- `python3 scripts/ksa_faith_utils.py prayer --city London --country "United Kingdom"`
- `python3 scripts/ksa_faith_utils.py eid-prayer --city Tokyo --country Japan --eid fitr`
