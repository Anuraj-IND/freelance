"""
Interactive location setup.

Asks for country / state / city and normalizes the names using the free
Nominatim (OpenStreetMap) API — no API key needed. It fixes spelling and
reveals aliases (e.g. "Allahabad" -> "Prayagraj").

- Country != India: location is just the country name.
- Country == India: location is "city, state, India" (state optional).
"""

import difflib
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "LeadFinder/1.0 (local lead research script)"}

# Known Indian states/UTs for reliable fuzzy matching (Nominatim is
# unreliable for misspelled state names).
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]


def _nominatim(params):
    params = {**params, "format": "json", "addressdetails": 1, "namedetails": 1, "limit": 5}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return []


def _aliases(item):
    """Collect alternate/localized names for a place, excluding its main name."""
    nd = item.get("namedetails", {}) or {}
    names = set()
    for key, value in nd.items():
        if key == "name" or key.startswith("name:"):
            if isinstance(value, str):
                names.add(value)
    alt = nd.get("alt_name")
    if alt:
        names.update(a.strip() for a in str(alt).split(";") if a.strip())
    main = item.get("name", "")
    names.discard(main)
    return sorted(names)[:6]


def _fuzzy_match_states(state):
    """Fuzzy-match a state name against the known Indian states list."""
    state = (state or "").strip()
    if not state:
        return "", []
    close = difflib.get_close_matches(state, INDIAN_STATES, n=1, cutoff=0.6)
    if not close:
        lower = state.lower().replace("u.p.", "uttar pradesh").replace("up", "uttar pradesh")
        close = difflib.get_close_matches(lower, INDIAN_STATES, n=1, cutoff=0.6)
    if not close:
        return state, []
    return close[0], []


def normalize_country(name):
    """Return the canonical country name."""
    name = (name or "").strip()
    if not name:
        return "India"
    results = _nominatim({"q": name, "featuretype": "country"})
    if results:
        return results[0].get("name") or name.title()
    return name.title()


def normalize_state(state):
    """Return canonical state name + aliases, or (state, []) if unknown."""
    state = (state or "").strip()
    if not state:
        return "", []
    return _fuzzy_match_states(state)


def normalize_city(city, state=""):
    """Return canonical city name + aliases, or (city, []) if unknown."""
    city = (city or "").strip()
    if not city:
        return "", []
    query = f"{city}, {state}, India" if state else f"{city}, India"
    results = _nominatim({"q": query, "featuretype": "city"})
    matches = [r for r in results if (r.get("address") or {}).get("state")]
    if not matches:
        # State may have been wrong — retry with city + country only
        results = _nominatim({"q": f"{city}, India", "featuretype": "city"})
        matches = [r for r in results if (r.get("address") or {}).get("state")]
    if not matches:
        results = _nominatim({"q": f"{city}, India"})
        matches = [r for r in results if (r.get("address") or {}).get("state")]
    if not matches:
        return city, []
    return matches[0].get("name") or city, _aliases(matches[0])


def choose_location():
    """
    Run the interactive prompts. Returns a location string to append to
    search queries (e.g. "Prayagraj, Uttar Pradesh, India" or "United States").
    """
    print("--- Location setup ---")

    country = input("Country (default: India): ").strip() or "India"
    country = normalize_country(country)
    print(f"  -> country: {country}")

    if country.strip().lower() != "india":
        return country

    state = input("State (e.g. Uttar Pradesh): ").strip()
    if state:
        state, state_aliases = normalize_state(state)
        if state_aliases:
            print(f"  -> state: {state} (also known as: {', '.join(state_aliases)})")
        else:
            print(f"  -> state: {state}")

    city = input("City (e.g. Prayagraj): ").strip()
    if city:
        corrected, city_aliases = normalize_city(city, state)
        if corrected and corrected.lower() != city.lower():
            label = corrected
            if city_aliases:
                label += f" (aka {', '.join(city_aliases)})"
            confirm = input(f"  Did you mean '{label}'? [Y/n]: ").strip().lower()
            if confirm != "n":
                city = corrected
        elif city_aliases:
            print(f"  -> city: {city} (also known as: {', '.join(city_aliases)})")

    parts = [p for p in (city, state, "India") if p]
    return ", ".join(parts) if parts else country
