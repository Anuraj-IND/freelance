# Lead Finder Pipeline

Finds local businesses with outdated/missing websites, scores them by opportunity,
and saves a lead sheet you can feed into an AI mail-writer.

## Setup (5 minutes)

1. Install Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Get a free Google Places API key:
   - Go to https://console.cloud.google.com/
   - Create a project, enable "Places API"
   - Create an API key (Credentials tab)
   - Google gives you a free monthly credit that covers a lot of test searches

3. Open `config.py` and:
   - Paste your API key into `GOOGLE_PLACES_API_KEY`
   - Edit `SEARCH_QUERIES` to the niches + city you want (add as many as you like)

4. Run it:
   ```
   python3 main.py
   ```

## What you get

Two output files:
- `leads_output.txt` — human-readable, one block per lead: business name, what they do,
  address, phone, email (if found on their site), current website, opportunity score,
  and a suggested offer line — sorted highest-opportunity first.
- `leads_output.json` — same data in JSON, ready to feed into an AI script later for
  auto-drafting personalized emails.

## Notes / limitations

- Google Places does not expose email addresses. Emails are extracted by scanning
  each business's own website (mailto links or plain-text regex on the homepage).
  Businesses with no website, or whose email isn't on the homepage, will show
  "Not found — check contact page manually."
- Website scoring is rule-based (no HTTPS, no mobile viewport, old footer year,
  broken/slow load, review count). This costs nothing to run. You can later replace
  `scorer.py`'s `score_lead()` with a local Ollama call for more nuanced judgment —
  the function signature is built so that's a drop-in swap.
- Google Places API has a free tier but does meter usage past a point — check your
  Cloud Console billing dashboard if you scale up search volume.
- Be considerate with request rate against target websites (the script already adds
  small delays) — don't hammer sites.

## Next step

Once you've got a lead sheet you trust, the `leads_output.json` file is what you'd
feed into an n8n/Make workflow (or another Claude/GPT script) to auto-draft a
personalized outreach message per lead using the `offer`, `score_reason`, and
`category` fields.
