"""
Config for the lead finder pipeline.

The API key lives in the .env file (gitignored) — never commit it.
Copy .env.example to .env if you need a template.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API key (Google AI Studio: https://aistudio.google.com/apikey)
# Loaded from .env — or set as an environment variable in your own way.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")

# Models to try, in order. If one hits a quota/traffic error, the script
# automatically fails over to the next model in the list.
GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
]

# What kind of businesses to search for (the location is now asked
# interactively when you run the script; the old city is ignored).
# Strategy: pick professions whose websites are usually missing/outdated —
# big brands are already fought over by agencies, these are not.
SEARCH_QUERIES = [
    ("dentist", ""),
    ("chiropractor", ""),
    ("electrician", ""),
    ("plumber", ""),
    ("roofing contractor", ""),
    ("HVAC repair service", ""),
    ("painter and decorator", ""),
    ("car repair garage", ""),
    ("auto mechanic", ""),
    ("driving school", ""),
    ("photographer", ""),
    ("wedding photographer", ""),
    ("event planner", ""),
    ("caterer", ""),
    ("bakery and cake shop", ""),
    ("beauty parlour", ""),
    ("salon", ""),
    ("spa and massage", ""),
    ("gym and fitness centre", ""),
    ("yoga studio", ""),
    ("tutoring centre", ""),
    ("computer coaching institute", ""),
    ("language classes", ""),
    ("chartered accountant", ""),
    ("tax consultant", ""),
    ("lawyer", ""),
    ("real estate agent", ""),
    ("interior designer", ""),
    ("architect", ""),
    ("property management", ""),
    ("travel agency", ""),
    ("packers and movers", ""),
    ("courier service", ""),
    ("laundry and dry cleaning", ""),
    ("tailor shop", ""),
    ("jewellery shop", ""),
    ("optometrist", ""),
    ("physiotherapist", ""),
    ("veterinary clinic", ""),
    ("pet groomers", ""),
    ("auditor and accountant", ""),
    ("small factory operator", ""),
    ("printing press", ""),
    ("signage and flex printing", ""),
    ("security services", ""),
    ("pest control", ""),
    ("carpenter", ""),
    ("welding workshop", " "),
    ("tile and marble supplier", ""),
    ("hardware shop", ""),
    ("fruit and vegetable wholesale", ""),
    ("grocery store", ""),
    ("general store", ""),
    ("mobile phone repair", ""),
    ("computer repair shop", ""),
    ("appliance repair service", ""),
    ("water purifier service", ""),
    ("e-rickshaw dealer", ""),
    ("cycle shop", ""),
    ("auto parts shop", ""),
    ("boutique ladies tailor", ""),
    ("embroidery unit", ""),
    ("ceramics and tiles unit", ""),
    ("ice cream parlour", ""),
    ("florist", ""),
    ("gifts shop", ""),
    ("stationery shop", ""),
    ("book store", ""),
    ("pharmacy", ""),
    ("medical store", ""),
    ("diagnostic lab", ""),
    ("x-ray clinic", ""),
    ("pathology lab", ""),
    ("garment manufacturer", ""),
    ("leather goods", ""),
    ("shoe store", ""),
    ("mobile accessories shop", ""),
    ("electronics repair shop", ""),
    ("UPS and inverter shop", ""),
    ("battery shop", ""),
    ("cable TV operator", ""),
    ("internet café", ""),
    ("cyber cafe and printing", ""),
    ("tent house and decoration", ""),
    ("machinery supplier", ""),
    ("pipe supplier", ""),
    ("cement shop", " "),
    ("building material supplier", ""),
    ("lumber supplier", ""),
    ("glass and mirror shop", ""),
    ("aluminium fabrication", ""),
    ("PVC furniture", ""),
    ("modular kitchen", ""),
    ("bathroom fittings shop", ""),
    ("lighting store", ""),
    ("home appliances store", ""),
    ("furniture store", ""),
    ("mattress shop", ""),
    ("kitchen items store", ""),
    ("utensils store", ""),
    ("clothes store", ""),
    ("textile shop", ""),
    ("linen store", ""),
]

# How many results to pull per query
MAX_RESULTS_PER_QUERY = 20

# Website audit settings
REQUEST_TIMEOUT_SECONDS = 8

# Output files
OUTPUT_TXT_PATH = "leads_output.txt"
OUTPUT_JSON_PATH = "leads_output.json"  # easier to feed into an AI mail-writer later