"""
Stage 1: Collect leads via the Gemini API.

Primary path: Gemini + Google Search grounding (live web data).
If grounding is quota-blocked on the free tier (RESOURCE_EXHAUSTED),
the collector automatically falls back to model-knowledge mode with a
strict anti-hallucination prompt.

Multiple models are tried in order: if a model errors out (quota, traffic,
unavailable), the next model in the list is tried automatically.

Note: email is NOT returned here; it is extracted later in auditor.py
by scanning each business's own website.
"""

import json
import re
import time
from google import genai
from google.genai import types

LEAD_JSON_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "address": {"type": "STRING"},
            "phone": {"type": "STRING"},
            "website": {"type": "STRING"},
            "rating": {"type": "NUMBER"},
            "review_count": {"type": "NUMBER"},
            "source_url": {"type": "STRING"},
        },
        "required": ["name"],
    },
}

GROUNDING_PROMPT = (
    "You are a local-business lead researcher. Use Google Search (you have "
    "real-time web access) to find genuine, verifiable businesses. Only return "
    "businesses that actually exist — cross-check that each one is real in "
    "search results before listing it. Return accurate data: real official "
    "website URL (or empty string if the business has no website), real phone "
    "number, and real review counts found in search results. For each "
    "business, set source_url to the URL of the page or listing where you "
    "found it (e.g. its Google Maps place link or directory listing). Do NOT "
    "invent websites, phone numbers, or review counts. If you cannot verify a "
    "field, return an empty string or 0."
)

NO_GROUNDING_PROMPT = (
    "You are listing well-known local businesses from your own knowledge. "
    "Only include businesses you are highly confident actually exist in that "
    "city. Never invent phone numbers, websites, or review counts — if you "
    "are not sure of a value, return an empty string or 0. Only provide an "
    "official website if you are certain it exists; otherwise leave it empty. "
    "For each business, set source_url to a Google Maps place link if you "
    "know one; otherwise leave it empty."
)


def _box_value(value, cast=None):
    """Pick the first non-empty value from a value that may be str/list/dict."""
    if isinstance(value, list):
        value = next((v for v in value if v), "")
    if isinstance(value, dict):
        value = value.get("0") or value.get("value") or ""
    if value is None:
        return ""
    if cast is float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return ""
    return str(value).strip()


def collect_leads(search_queries, api_key, max_results_per_query=20, models=None):
    """
    Run all search queries through Gemini and return a flat list of lead dicts
    with basic info.
    Each lead: name, category, address, phone, website, rating, review_count

    `models` is an ordered list of model names; on failure the next one is
    tried automatically.
    """
    if not models:
        models = ["gemini-3.5-flash"]
    client = genai.Client(api_key=api_key)
    all_leads = []
    state = {
        "grounding_available": True,   # grounding quota is model-independent
        "working_model": None,          # last model that succeeded — try it first
        "failed_models": set(),         # models that errored — skip for the rest of the run
    }

    for niche, location in search_queries:
        prompt = (
            f"Find {max_results_per_query} real {niche} businesses in "
            f"{location}. Return a JSON array of exactly "
            f"{max_results_per_query} objects with keys: name, address, phone, "
            f"website, rating, review_count, source_url. The 'website' value "
            f"must be a full URL starting with http:// or https://, or an "
            f"empty string if there is no website. The 'source_url' value "
            f"must be the link to the page/listing where you found the "
            f"business (Google Maps place link preferred)."
        )

        print(f"[collect] Gemini: {niche} in {location}")
        leads, used_grounding, used_model = _query_with_failover(
            client, models, prompt, state
        )
        if not state["grounding_available"]:
            print("  (grounding quota unavailable — using model knowledge mode)")
        print(f"  -> {len(leads)} results (via {used_model})")

        for lead in leads:
            source_url = _box_value(lead.get("source_url"))
            if not source_url:
                source_url = _maps_search_link(
                    _box_value(lead.get("name")),
                    _box_value(lead.get("address")),
                    location,
                )
            all_leads.append({
                "name": _box_value(lead.get("name")),
                "category": niche,
                "address": _box_value(lead.get("address")),
                "phone": _box_value(lead.get("phone")),
                "website": _box_value(lead.get("website")),
                "rating": _box_value(lead.get("rating"), float),
                "review_count": _box_value(lead.get("review_count")),
                "source_url": source_url,
            })

        time.sleep(1)

    return all_leads


def _candidates(models, state):
    """Ordered list of models to try: last-working first, failures skipped."""
    ordered = []
    if state["working_model"]:
        ordered.append(state["working_model"])
    ordered += [m for m in models if m != state["working_model"]]
    return [m for m in ordered if m not in state["failed_models"]] or models[:1]


def _query_with_failover(client, models, prompt, state):
    """
    Try models in order. A model that errors is skipped and the next one is
    tried. Sticky state (passed by caller) remembers working/failed models
    across queries so the same dead model isn't retried every time.
    Returns (leads, used_grounding, used_model).
    """
    for model in _candidates(models, state):
        if state["grounding_available"]:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GROUNDING_PROMPT,
                        response_mime_type="application/json",
                        response_schema=LEAD_JSON_SCHEMA,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                )
                leads = _parse_leads_json(getattr(response, "text", "") or "")
                if leads:
                    state["working_model"] = model
                    return leads, True, model
            except Exception as e:
                print(f"  [!] {model} grounding failed: {_short_error(e)}")
                if _is_quota_error(e):
                    state["grounding_available"] = False

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=NO_GROUNDING_PROMPT,
                    response_mime_type="application/json",
                    response_schema=LEAD_JSON_SCHEMA,
                ),
            )
            leads = _parse_leads_json(getattr(response, "text", "") or "")
            if leads:
                state["working_model"] = model
                return leads, False, model
            print(f"  [!] {model} returned no usable leads")
        except Exception as e:
            print(f"  [!] {model} failed: {_short_error(e)}")
            state["failed_models"].add(model)

    print(f"  [!] All {len(models)} models failed for this query")
    return [], False, models[0]


def _short_error(e):
    return str(e)[:160]


def _maps_search_link(name, address, location):
    """
    Build a Google Maps search URL for a business. Always works, no API key
    needed — opens the business listing which shows its phone number.
    """
    query_parts = [p for p in (name, address, location) if p]
    query = " ".join(query_parts)
    if not query:
        return ""
    return "https://www.google.com/maps/search/?api=1&query=" + query.replace(" ", "+")


def _is_quota_error(e):
    return "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)


def _parse_leads_json(raw):
    """Parse Gemini JSON output, tolerating markdown fences or stray text."""
    if not raw:
        return []
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        data = data.get("leads") or data.get("results") or data.get("data") or []
    if not isinstance(data, list):
        return []
    return data