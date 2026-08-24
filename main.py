"""
Run the full pipeline: collect -> audit -> score -> save.

Usage:
    python3 main.py

Make sure you've set GEMINI_API_KEY in config.py first.
"""

import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import config
from geo import choose_location
from collector import collect_leads
from auditor import audit_website
from scorer import score_lead, get_offer_text


def run_pipeline(location=None, search_queries=None, max_results=None, log=print, audio_dir=None):
    """
    Run collect -> audit -> score -> save.

    location:        location string (e.g. "Prayagraj, Uttar Pradesh, India").
                     If None, asks interactively via geo.choose_location().
    search_queries:  list of (niche, location) tuples. If None, built from
                     config.SEARCH_QUERIES with the chosen location.
    max_results:     results per query. If None, uses config.
    log:             callable used for progress messages (default print).
    """
    if config.GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        log("!! Set your GEMINI_API_KEY in config.py before running.")
        return []

    # --- Stage 0: Ask where to search (only if not provided) ---
    if location is None:
        location = choose_location()
    log(f"Target location: {location}\n")

    if search_queries is None:
        search_queries = [(niche, location) for niche, _ in config.SEARCH_QUERIES]
    else:
        search_queries = [(niche, location) for niche, _ in search_queries]
    if max_results is None:
        max_results = config.MAX_RESULTS_PER_QUERY

    # --- Stage 1: Collect ---
    log("=== Stage 1: Collecting leads ===")
    leads = collect_leads(
        search_queries,
        config.GEMINI_API_KEY,
        max_results,
        config.GEMINI_MODELS,
    )
    log(f"Collected {len(leads)} total leads.\n")

    # --- Stage 2 + 3: Audit + Score each lead ---
    log("=== Stage 2 & 3: Auditing websites and scoring ===")
    enriched_leads = []
    for i, lead in enumerate(leads, 1):
        log(f"[{i}/{len(leads)}] Auditing: {lead['name']}")
        audit = audit_website(lead["website"], config.REQUEST_TIMEOUT_SECONDS)
        score, reason = score_lead(lead, audit)
        offer = get_offer_text(lead["category"])

        enriched_leads.append({
            **lead,
            "email": audit["email_found"],
            "opportunity_score": score,
            "score_reason": reason,
            "offer": offer,
        })

    # Sort by opportunity score, highest first — highest score on top
    enriched_leads.sort(key=lambda x: x["opportunity_score"], reverse=True)

    # --- Save outputs ---
    save_txt(enriched_leads, config.OUTPUT_TXT_PATH)
    save_json(enriched_leads, config.OUTPUT_JSON_PATH)

    log(f"\nDone. {len(enriched_leads)} leads written to:")
    log(f"  - {config.OUTPUT_TXT_PATH}  (human-readable)")
    log(f"  - {config.OUTPUT_JSON_PATH} (for feeding into an AI mail-writer later)")
    return enriched_leads


def save_txt(leads, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, lead in enumerate(leads, 1):
            f.write(f"LEAD #{i}\n")
            f.write(f"Business Name : {lead['name']}\n")
            f.write(f"What They Do  : {lead['category']}\n")
            f.write(f"Address       : {lead['address']}\n")
            f.write(f"Phone         : {lead['phone'] or 'Not available'}\n")
            f.write(f"Email         : {lead['email'] or 'Not found - check contact page manually'}\n")
            f.write(f"Current Site  : {lead['website'] or 'No website'}\n")
            f.write(f"Source Link   : {lead.get('source_url') or 'N/A'}\n")
            f.write(f"Opportunity   : {lead['opportunity_score']}/100 ({lead['score_reason']})\n")
            f.write(f"What We Offer : {lead['offer']}\n")
            f.write("-" * 60 + "\n\n")


def save_json(leads, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    run_pipeline()
