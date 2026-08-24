"""
Web UI for the lead pipeline.

Run:  python app.py   ->  http://127.0.0.1:5000
"""

import json
import os
import threading
from flask import Flask, jsonify, render_template, request

import config
import main

app = Flask(__name__)

PIPELINE = {
    "running": False,
    "phase": "idle",
    "logs": [],
    "location": "",
    "error": None,
}


def _log(msg):
    PIPELINE["logs"].append(str(msg))
    if len(PIPELINE["logs"]) > 500:
        PIPELINE["logs"] = PIPELINE["logs"][-500:]


def _run_in_background(location, niches, max_results):
    def worker():
        try:
            PIPELINE["running"] = True
            PIPELINE["phase"] = "running"
            PIPELINE["logs"] = []
            PIPELINE["error"] = None
            PIPELINE["location"] = location
            search_queries = [(n, location) for n in niches]
            main.run_pipeline(
                location=location,
                search_queries=search_queries,
                max_results=max_results,
                log=_log,
            )
            PIPELINE["phase"] = "done"
        except Exception as exc:  # pragma: no cover - defensive
            PIPELINE["error"] = str(exc)
            _log(f"!! Pipeline error: {exc}")
        finally:
            PIPELINE["running"] = False

    threading.Thread(target=worker, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html", niches=config.SEARCH_QUERIES)


@app.route("/api/run", methods=["POST"])
def api_run():
    if PIPELINE["running"]:
        return jsonify({"ok": False, "error": "Pipeline already running."}), 409

    data = request.get_json(force=True)
    country = (data.get("country") or "").strip() or "India"
    location = country.strip()
    if country.strip().lower() == "india":
        state = (data.get("state") or "").strip()
        city = (data.get("city") or "").strip()
        parts = [p for p in (city, state, "India") if p]
        if parts:
            location = ", ".join(parts)

    niches = [n for n in data.get("niches", []) if n.strip()]
    if not niches:
        niches = [n for n, _ in config.SEARCH_QUERIES]
    max_results = int(data.get("max_results") or config.MAX_RESULTS_PER_QUERY)

    _run_in_background(location, niches, max_results)
    return jsonify({"ok": True, "location": location, "niches": len(niches)})


@app.route("/api/status")
def api_status():
    leads = []
    try:
        if os.path.exists(config.OUTPUT_JSON_PATH):
            with open(config.OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
                leads = json.load(f)
    except (json.JSONDecodeError, OSError):
        leads = []
    return jsonify({
        "running": PIPELINE["running"],
        "phase": PIPELINE["phase"],
        "logs": PIPELINE["logs"],
        "location": PIPELINE["location"],
        "error": PIPELINE["error"],
        "leads": leads,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)