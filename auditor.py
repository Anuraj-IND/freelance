"""
Stage 2: Audit each lead's website (if they have one) and try to extract an email.
No paid APIs needed here — just requests + basic parsing.
"""

import re
import datetime
import requests
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
CURRENT_YEAR = datetime.datetime.now().year


def audit_website(url, timeout=8):
    """
    Returns a dict describing the state of the website:
    has_website, is_https, has_mobile_viewport, footer_year, email_found, audit_notes
    """
    result = {
        "has_website": False,
        "is_https": False,
        "has_mobile_viewport": False,
        "footer_year": None,
        "email_found": "",
        "load_ok": False,
        "notes": [],
    }

    if not url:
        result["notes"].append("No website listed on Google — needs a site built from scratch.")
        return result

    result["has_website"] = True
    result["is_https"] = url.strip().lower().startswith("https://")

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LeadAuditBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        result["load_ok"] = resp.status_code == 200
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Mobile viewport check
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        result["has_mobile_viewport"] = viewport_tag is not None

        # Try to find a copyright year in the footer (or anywhere on page as fallback)
        footer = soup.find("footer")
        search_text = footer.get_text() if footer else html
        year_matches = re.findall(r"(20\d{2})", search_text)
        valid_years = [int(y) for y in year_matches if int(y) <= CURRENT_YEAR]
        if valid_years:
            result["footer_year"] = min(valid_years)

        # Try to find an email — check mailto links first, then plain text
        mailto_links = [a["href"].replace("mailto:", "").split("?")[0]
                         for a in soup.find_all("a", href=True) if a["href"].startswith("mailto:")]
        if mailto_links:
            result["email_found"] = mailto_links[0]
        else:
            found = EMAIL_REGEX.findall(html)
            if found:
                result["email_found"] = found[0]

        if not result["has_mobile_viewport"]:
            result["notes"].append("Not mobile-responsive.")
        if not result["is_https"]:
            result["notes"].append("No HTTPS/SSL.")
        if result["footer_year"] and result["footer_year"] <= CURRENT_YEAR - 3:
            result["notes"].append(f"Footer/copyright year is old ({result['footer_year']}).")
        if not result["email_found"]:
            result["notes"].append("No email found on homepage — check contact page manually.")

    except requests.RequestException as e:
        result["notes"].append(f"Could not load site ({type(e).__name__}) — may be down or blocking bots.")

    return result
