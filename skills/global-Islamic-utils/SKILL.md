---
name: ksa-faith-utils
description: local-focused Islamic date and prayer utility for OpenClaw. It handles prayer times, Hijri↔Gregorian conversion, local Eid estimates, and DuckDuckGo-based web/news lookup for local announcements.
user-invocable: true
---

# Global Faith Utils

Use this skill when the user asks about local prayer times, Hijri dates, Eid timing, or quick DuckDuckGo-backed local news lookups.

This skill is designed for local Arabia first:
- local city names are accepted in Arabic or English.
- Prayer timings use AlAdhan city timings with a local-relevant calculation method.
- Hijri conversions are useful for Umm al-Qura style daily tasks.
- Eid support includes an estimated prayer time and current web results to help verify local announcements.

## Files

- `scripts/ksa_faith_utils.py` — main helper CLI
- `references/README.md` — install and usage notes

## When to use

Use this skill for requests such as:
- "متى أذان المغرب في الرياض؟"
- "حوّل 1 شوال 1447 إلى ميلادي"
- "متى صلاة العيد في جدة؟"
- "هات أخبار إعلان صلاة العيد في الرياض"
- "ابحث عن خبر رسمي عن العيد من وكالة الأنباء السعودية"

## Important behavior

### Prayer times
Run:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py prayer --city Riyadh
```

You can also pass a date:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py prayer --city "الرياض" --date 30-03-2026
```

Expected output is JSON with:
- city
- gregorian
- hijri
- fajr
- sunrise
- dhuhr
- asr
- maghrib
- isha
- timezone

### Hijri conversion
Gregorian to Hijri:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py hijri --date 30-03-2026
```

Hijri to Gregorian:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py hijri --day 1 --month 10 --year 1447
```

### Next Eid
Get the next Eid estimate for a city:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py next-eid --city Riyadh
```

This returns:
- Eid type
- estimated Gregorian date
- estimated prayer time
- days until
- supporting web/news links

### Eid prayer time
Get a city-specific Eid estimate and related web results:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py eid-prayer --city Jeddah --eid fitr --year 2026
```

**Important:** the script estimates Eid prayer as `sunrise + 15 minutes` and also fetches web results. Treat it as a starting point, then verify against local mosque statements or official local channels.

### DuckDuckGo web search
General search:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py news "صلاة عيد الفطر الرياض 2026"
```

Search only a specific site, such as SPA:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py news "صلاة العيد الرياض" --site spa.gov.sa
```

### Read a webpage
After search returns a good link, read the page text:

```bash
python3 skills/ksa-faith-utils/scripts/ksa_faith_utils.py read "https://example.com/article"
```

## Agent workflow

When a user asks about prayer times:
1. Run the `prayer` command.
2. Summarize only the relevant prayer unless the user wants all timings.
3. Mention the date and city in the answer.

When a user asks for Hijri conversion:
1. Run the `hijri` command.
2. Return both calendars clearly.
3. Keep the answer short unless the user asks for details.

When a user asks about Eid prayer:
1. Run `eid-prayer` or `next-eid`.
2. Clearly label the time as an estimate.
3. If the result includes links from trusted local sources, mention them first.
4. If web results are weak, say you could not confirm an official local post yet.

When a user asks for local news around Eid, Ramadan, moonsighting, or ministry announcements:
1. Run `news` with Arabic and/or English phrasing.
2. Prefer official local sources when possible, such as `spa.gov.sa`, ministry sites, or municipality pages.
3. Optionally run `read` on the best result.
4. Quote only short excerpts and summarize the rest.

## Safety and quality notes

- Do not present the Eid estimate as an official confirmed mosque schedule.
- Do not invent official announcements when search results are unclear.
- Prefer official domains when discussing religious dates or public guidance.
- Keep results local to local cities unless the user explicitly asks about another country.

## Example prompts

- "متى المغرب اليوم في جدة؟"
- "1 رمضان 1447 كم يوافق ميلادي؟"
- "كم باقي على العيد في الرياض؟"
- "ابحث عن خبر رسمي عن صلاة العيد في مكة"
- "هات لي روابط خبر صلاة عيد الفطر في الدمام"


## Worldwide update
- The skill now supports any city worldwide by passing both `--city` and `--country`.
- Saudi Arabic aliases are still supported for convenience.
