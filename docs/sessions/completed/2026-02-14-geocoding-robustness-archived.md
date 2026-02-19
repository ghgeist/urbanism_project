# Backlog: More robust address geocoding

**Created:** 2026-02-14  
**Archived:** 2026-02-19  
**Archived Reason:** Addressed via US Census Bureau fallback geocoder (different approach than originally recommended, but solves the same problem)

## Problem

Users can enter addresses in the app (address, city, ZIP, etc.). Geocoding is done via **Nominatim** (OpenStreetMap) with `country_codes='us'`. In some cases the service returns no result and the user sees "Could not find that location."

Observed causes include:

- **Spelling variants:** Nominatim does exact/substring matching. OSM data in the US often uses US spelling (e.g. "harbor"). If the user types a UK variant (e.g. "harbour"), the query may not match and geocoding fails.
- **Formatting / typos:** Minor typos or non-standard formatting can prevent a match.
- **Strict matching:** Nominatim does not provide fuzzy or typo-tolerant search.

No user data or specific addresses are stored or logged; the issue is the geocoder's sensitivity to spelling and format.

## Solution Implemented

**Status:** ✅ Addressed via US Census Bureau fallback geocoder

Instead of switching to Photon (as originally recommended), the implementation added a **US Census Bureau Geocoding API fallback** that automatically triggers when Nominatim returns no result. This approach:

- Maintains Nominatim as primary geocoder (good for cities, ZIP codes, neighborhoods)
- Adds Census Bureau fallback for full US street addresses (comprehensive coverage)
- Handles UK→US spelling normalization (e.g., "harbour" → "harbor")
- No API key required, free service
- Implemented in `services/walkability.py` with `_geocode_via_census()` function

**Implementation details:**
- See `docs/dev_notes/2026-02-19.md` for full implementation notes
- See `services/walkability.py` for `_geocode_via_census()` and `get_location()` functions
- See `tests/test_walkability.py` for test coverage

**Original Options Considered:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Photon (geopy)** | Switch from Nominatim to **Photon** (OSM-based, Elasticsearch backend). Geopy includes `geopy.geocoders.Photon`. Photon supports fuzzy/typo-tolerant search. Use `bbox` to bias results to the continental US. | Same OSM data; built-in fuzzy matching; no API key; single geocoder call. | Public Komoot server has usage limits; no strict country filter (bbox only). |
| **US Census Geocoder** ✅ **CHOSEN** | Use the US Census Bureau's free geocoding API (REST or e.g. `census-geocoder` package) for US addresses. | Purpose-built for US addresses; no API key; good for structured addresses. | New dependency or HTTP client code; different API shape; US-only. |
| **Nominatim + spelling fallback** | Keep Nominatim; on failure, normalize a small set of UK→US spellings (e.g. harbour→harbor) and retry once. | Minimal change; no new service. | Not robust (only handles a fixed word list); brittle and maintenance-heavy. |
| **Photon as fallback** | Keep Nominatim as primary; if it returns no result, call Photon with the same query (with US bbox). | Improves robustness without dropping Nominatim. | Two services to maintain; two calls when Nominatim fails. |
| **Paid geocoder** | Use a commercial geocoder (e.g. Google, Mapbox) with fuzzy matching. | Very robust matching. | API key, cost, and ToS; may be unnecessary for current scale. |

## References

- Current geocoding: `services/walkability.py` — `get_location()` and `_geocode_via_census()`
- Implementation notes: `docs/dev_notes/2026-02-19.md`
- US Census Geocoder: https://geocoding.geo.census.gov/geocoder/
- Lessons: `docs/dev_notes/lessons.md` (entry on geocoding / spelling)
