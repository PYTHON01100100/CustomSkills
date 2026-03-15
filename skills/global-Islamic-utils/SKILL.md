---
name: global-Islamic-utils
description: Global Islamic calendar and prayer utility. Handles prayer times, Qiyam al-Layl, Hijri↔Gregorian conversion, Eid al-Fitr, Eid al-Adha, Yawm Arafah, hilal moon sighting (country-specific announced dates), day virtues, and Google News lookups. Works for any city and country worldwide.
user-invocable: true
---

# Global Islamic Utils

Use this skill when the user asks about prayer times, Islamic dates, Qiyam, Eid, Yawm Arafah, hilal moon sighting, or the Islamic significance of a day — for any city or country worldwide.

## Key principle: hilal-aware dates

Eid al-Fitr, Eid al-Adha, Yawm Arafah, and Ramadan start depend on actual moon (hilal) sighting, which differs by country:

- Saudi Arabia might sight the hilal on Tuesday → Eid on Wednesday
- Syria might sight it on Wednesday → Eid on Thursday
- Some countries follow Saudi Arabia; others do their own local sighting

This skill always:
1. Returns the **calculated date** (Umm al-Qura astronomical calculation)
2. Searches Google News for the **officially announced date** for the specific country
3. Returns `date_status: "announced"` or `"calculated (Umm al-Qura — unconfirmed)"`
4. Uses the **announced date** for all prayer time calculations when found

**Yawm Arafah always follows Saudi Arabia's announcement** (Hajj is in Mecca regardless of the user's country).

## Files

- `scripts/islamic_faith_utils.py` — main helper CLI
- `references/README.md` — install notes

## When to use

Use this skill for requests such as:
- "متى أذان المغرب في الرياض؟"
- "ما هي فضائل يوم الجمعة؟"
- "متى يبدأ وقت القيام في جدة الليلة؟"
- "متى صلاة عيد الفطر في سوريا؟"
- "هل رأت السعودية الهلال؟ متى العيد؟"
- "متى يوم عرفة 2026؟"
- "كم باقي على العيد في تركيا؟"
- "حوّل 1 شوال 1447 إلى ميلادي"

---

## Commands

### prayer — Daily prayer times

```bash
python scripts/islamic_faith_utils.py prayer --city Riyadh
python scripts/islamic_faith_utils.py prayer --city Damascus --country Syria
python scripts/islamic_faith_utils.py prayer --city London --country "United Kingdom" --date 30-03-2026
```

Returns: `city`, `country`, `gregorian`, `hijri`, `weekday_en`, `weekday_ar`, `fajr`, `sunrise`, `dhuhr`, `asr`, `maghrib`, `isha`, `midnight`, `method`, `timezone`

---

### day-info — Islamic significance of the day

Returns the Islamic virtues and history for today's weekday (Friday, Monday, etc.) plus prayer times.

```bash
python scripts/islamic_faith_utils.py day-info --city Riyadh
python scripts/islamic_faith_utils.py day-info --city Cairo --country Egypt --date 13-03-2026
```

Returns: `weekday_en`, `weekday_ar`, `gregorian`, `hijri`, `virtues` (list), `recommended_acts` (list), `prayer_times`

Example virtues output for Friday:
- "The best day on which the sun rises is Friday. (Muslim)"
- "There is an hour on Friday during which any du'aa is answered. (Bukhari, Muslim)"
- "Reading Surah Al-Kahf on Friday gives light between the two Fridays. (Hakim)"

Example recommended_acts for Monday:
- "Fasting — Sunnah of the Prophet ﷺ."
- "Deeds are presented to Allah on Monday and Thursday. (Tirmidhi)"

---

### qiyam — Qiyam al-Layl (last third of night)

Calculates the start of the last third of the night (Maghrib → Fajr) — the best time for Qiyam al-Layl.

```bash
python scripts/islamic_faith_utils.py qiyam --city Riyadh
python scripts/islamic_faith_utils.py qiyam --city Istanbul --country Turkey --date 20-03-2026
```

Returns: `maghrib`, `isha`, `fajr_next_day`, `night_duration`, `last_third_starts`, `last_third_ends_at_fajr`

---

### hijri — Gregorian ↔ Hijri conversion

Gregorian to Hijri:

```bash
python scripts/islamic_faith_utils.py hijri --date 20-03-2026
```

Hijri to Gregorian:

```bash
python scripts/islamic_faith_utils.py hijri --day 1 --month 10 --year 1447
```

---

### hilal — Moon sighting + announced month start

Searches news for the officially announced start of a Hijri month for a specific country and compares it to the calculated Umm al-Qura date.

```bash
python scripts/islamic_faith_utils.py hilal --country "Saudi Arabia" --month shawwal
python scripts/islamic_faith_utils.py hilal --country Syria --month ramadan
python scripts/islamic_faith_utils.py hilal --country Morocco --month dhulhijja --year 2026
```

Valid month keys: `muharram`, `safar`, `rabiulawal`, `rabiulakhir`, `jumadalawal`, `jumadalakhir`, `rajab`, `shaban`, `ramadan`, `shawwal`, `dhulqada`, `dhulhijja`

Returns: `calculated_start_gregorian`, `hilal_eve_gregorian` (29th of prev month), `announced_start_gregorian` (from news, or null), `date_used`, `date_status`, `announcement_source`, `moon_sighting_news`

**Example showing country difference:**
- Saudi Arabia: `announced=20-03-2026` (Eid Wednesday)
- Syria: `announced=19-03-2026` (Eid Tuesday — saw hilal one day earlier)
- Morocco: `announced=null` → falls back to calculated

---

### eid-prayer — Eid prayer time (hilal-aware)

Searches for the country's official hilal announcement, uses the announced date if found (otherwise calculated), then estimates prayer as Sunrise + 15 minutes.

```bash
python scripts/islamic_faith_utils.py eid-prayer --city Riyadh --eid fitr
python scripts/islamic_faith_utils.py eid-prayer --city Damascus --country Syria --eid fitr --year 2026
python scripts/islamic_faith_utils.py eid-prayer --city Cairo --country Egypt --eid adha
```

Returns: `eid`, `calculated_date`, `announced_date`, `date_used`, `date_status`, `estimated_prayer_time`, `prayer_basis`, `announcement_source`, `announcement_link`, `supporting_news_results`

**Important:** Prayer time is estimated as Sunrise + 15 minutes on `date_used`. Always verify with the local mosque or official announcement.

---

### arafah — Yawm Arafah (9th Dhul Hijjah)

Arafah **always follows Saudi Arabia's official Dhul Hijjah announcement** regardless of which country/city you request — because Hajj is in Mecca.

```bash
python scripts/islamic_faith_utils.py arafah --city Riyadh
python scripts/islamic_faith_utils.py arafah --city Jakarta --country Indonesia
python scripts/islamic_faith_utils.py arafah --city London --country "United Kingdom" --year 2026
```

Returns: `event`, `hijri_date`, `calculated_date`, `announced_date`, `date_used`, `date_status`, `weekday_en`, `weekday_ar`, `fasting_virtue`, `note`, `prayer_times`, `announcement_source`

**Fasting virtue:** Fasting on Arafah expiates the sins of the previous and coming year. (Muslim 1162) — for non-pilgrims only.

---

### next-eid — Next upcoming Eid

Returns the next Eid (Fitr or Adha) that has not yet passed. Automatically checks next year if both current-year Eids have passed.

```bash
python scripts/islamic_faith_utils.py next-eid --city Riyadh
python scripts/islamic_faith_utils.py next-eid --city Ankara --country Turkey
```

Returns same fields as `eid-prayer` plus `days_until`.

---

### next-events — All 3 upcoming major events

Returns the next Yawm Arafah, Eid al-Fitr, and Eid al-Adha sorted by date — the complete picture at a glance.

```bash
python scripts/islamic_faith_utils.py next-events --city Riyadh
python scripts/islamic_faith_utils.py next-events --city Kuala Lumpur --country Malaysia
```

Example output:
```
Eid al-Fitr             20-03-2026   5 days
Yawm Arafah (Arafah)    26-05-2026  72 days
Eid al-Adha             27-05-2026  73 days
```

---

### news — Google News search

Searches Google News RSS (Arabic or English locale auto-detected from query).

```bash
python scripts/islamic_faith_utils.py news "Eid al-Fitr 2026 Saudi Arabia"
python scripts/islamic_faith_utils.py news "صلاة عيد الفطر الرياض 2026"
python scripts/islamic_faith_utils.py news "صلاة العيد الرياض" --site spa.gov.sa
python scripts/islamic_faith_utils.py news "moon sighting 2026" --max-results 10
```

Returns: list of `{title, link, snippet}` with real article URLs and publication date.

---

### read — Read a webpage

```bash
python scripts/islamic_faith_utils.py read "https://example.com/article"
python scripts/islamic_faith_utils.py read "https://spa.gov.sa/article" --max-chars 8000
```

---

## Agent workflows

### When a user asks about prayer times
1. Run `prayer`.
2. Report only the requested prayer (e.g. Maghrib) unless all are requested.
3. Mention the city, date, and Hijri date.

### When a user asks about the significance of today or a specific day
1. Run `day-info`.
2. Highlight the virtues and recommended acts.
3. Include prayer times if relevant.

### When a user asks about Qiyam / Tahajjud time
1. Run `qiyam`.
2. Report `last_third_starts` and `last_third_ends_at_fajr`.
3. Remind the user this is the best period for voluntary night prayer.

### When a user asks about Eid (Fitr or Adha)
1. Run `eid-prayer` or `next-eid`.
2. Check `date_status`:
   - If `"announced"`: state the confirmed date and source.
   - If `"calculated (Umm al-Qura — unconfirmed)"`: clearly say the date is estimated and not yet confirmed for that country.
3. Note that different countries may have different dates based on local hilal sighting.
4. Label the prayer time as an estimate (Sunrise + 15 min).

### When a user asks about Yawm Arafah
1. Run `arafah`.
2. Mention the fasting virtue (expiates two years of sins — for non-pilgrims).
3. Note that the date follows Saudi Arabia's announcement regardless of country.

### When a user asks when Ramadan or a Hijri month starts in a specific country
1. Run `hilal --country <country> --month <month>`.
2. If `announced_start_gregorian` is found: present it as the confirmed date with the source.
3. If null: present `calculated_start_gregorian` as the expected date and say the official announcement has not been found yet.
4. If relevant: run `news` with local-language terms to find more recent announcements.

### When a user asks to compare Eid dates across countries
1. Run `hilal` for each country separately.
2. Compare `announced_start_gregorian` (or `date_used` as fallback).
3. Explain the difference is due to local hilal sighting.

### When a user asks for news or official announcements
1. Run `news` with Arabic and English terms.
2. For official Saudi sources try `--site spa.gov.sa`.
3. Run `read` on the best result if a deeper excerpt is needed.
4. Quote short excerpts only; summarize the rest.

---

## Safety and quality notes

- Never present a calculated date as a confirmed announcement.
- Always check `date_status` before presenting Eid or Ramadan dates — if `"unconfirmed"`, say so explicitly.
- Do not invent official announcements when search results are empty.
- Eid prayer time (Sunrise + 15 min) is an estimate — always direct the user to verify with their local mosque.
- For Arafah fasting: only mention it as recommended for those NOT performing Hajj.
- Prefer official sources: `spa.gov.sa` (Saudi), ministry of endowments sites, or official national news agencies.

---

## Example prompts

**Prayer times:**
- "متى المغرب اليوم في جدة؟"
- "What are the prayer times in London tomorrow?"
- "prayer times for Tokyo Japan"

**Day info:**
- "ما فضل يوم الجمعة؟"
- "What is special about Monday in Islam?"
- "يوم الأربعاء له فضل؟"

**Qiyam:**
- "متى يبدأ وقت القيام الليلة في الرياض؟"
- "What time is Tahajjud in Makkah tonight?"

**Hijri conversion:**
- "1 رمضان 1447 كم يوافق ميلادي؟"
- "Convert 20 March 2026 to Hijri"

**Hilal / Moon sighting:**
- "هل رأت سوريا هلال شوال؟ متى العيد؟"
- "When does Ramadan start in Morocco 2026?"
- "Did Saudi Arabia confirm the Shawwal hilal?"

**Eid:**
- "متى صلاة عيد الفطر في الرياض 2026؟"
- "Eid al-Adha prayer time in Cairo 2026"
- "كم باقي على العيد في تركيا؟"

**Arafah:**
- "متى يوم عرفة 2026؟"
- "When is Yawm Arafah? Should I fast?"
- "يوم عرفة 1447 كم يوافق ميلادي؟"

**All upcoming events:**
- "ما هي المناسبات الإسلامية القادمة؟"
- "Show me the next Eid and Arafah dates"
