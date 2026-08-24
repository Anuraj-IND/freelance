"""
Stage 3: Score and prioritize leads.

Rule-based to start (zero cost). Swap this out for a local Ollama call later
if you want more nuanced "trust score" judgments — the function signature
below is designed so that's a drop-in replacement.
"""

CATEGORY_OFFER_TEMPLATES = {
    # --- Medical / health ---
    "dentist": "A clean, mobile-friendly site with online appointment booking, service list, and patient trust signals (certifications, before/after photos).",
    "chiropractor": "A modern one-page site with booking widget, treatment list, and patient testimonials.",
    "physiotherapist": "A trust-building clinic site with treatment list, booking form, and patient success stories.",
    "optometrist": "A clean site with eye-care services, frame/brand showcase, and appointment booking.",
    "veterinary clinic": "A pet-friendly clinic site with services, emergency info, and appointment booking.",
    "pet groomers": "A friendly site with service menu, before/after grooming photos, and online booking.",
    "pharmacy": "A local pharmacy site with medicine order/enquiry form, timings, and delivery info.",
    "medical store": "A simple site with stock enquiry, home delivery info, and prescription upload.",
    "diagnostic lab": "A lab site with test catalogue, rate list, home-pickup enquiry, and report status.",
    "x-ray clinic": "A clinic site with test/services list, timings, and online booking form.",
    "pathology lab": "A lab site with test-price list, home pickup service, and report delivery status.",
    "spa and massage": "A relaxing one-page site with treatment menu, pricing, and online booking.",
    "gym and fitness centre": "A high-energy site with membership plans, trainer profiles, and free-trial signup.",
    "yoga studio": "A calm, modern site with class schedule, instructor bio, and trial class signup.",
    "wellness centre": "A serene site with program list, pricing, and consultation booking.",
    "wellness clinic": "A serene site with program list, pricing, and consultation booking.",

    # --- Home services ---
    "electrician": "A simple mobile-first site with service areas, emergency contact button, and a photo gallery of past work.",
    "plumber": "A mobile-first site with service list, 24/7 emergency call button, service areas, and past-job gallery.",
    "roofing contractor": "A project-portfolio site with roof types offered, free quote form, and before/after photos.",
    "HVAC repair service": "A service site with AC/heater repair list, emergency call button, and maintenance plans.",
    "painter and decorator": "A portfolio-style site with colour palettes, past-work gallery, and instant quote form.",
    "carpenter": "A services-and-gallery site with a quote request form, furniture/repair services listed fast.",
    "interior designer": "A visually-driven portfolio site with project galleries and a contact/inquiry form.",
    "beauty parlour": "A glam, modern site with service menu, bridal packages, and appointment booking.",
    "salon": "A stylish site with service & price list, barber/stylist profiles, and online booking.",
    "welding workshop": "A workshop site with welding services gallery, custom fabrication enquiry, and quote.",
    "aluminium fabrication": "A fabrication site with product range, glass-door/window solutions, and quote form.",
    "pest control": "A service site with pest list, treatment packages, and instant booking form.",
    "water purifier service": "A service site with RO/AMC plans, filter replacement, filter enquiry and doorstep booking.",
    "appliance repair service": "A repair site with appliances covered, doorstep booking, and fast callback form.",
    "mobile phone repair": "A repair shop site with repair & price list, brand dropdown, and pickup booking.",
    "computer repair shop": "A tech-repair site with services list, turnaround promise, and booking form.",
    "electronics repair shop": "A repair site with device list, job-status tracking, and booking form.",
    "internet café": "A simple site with printing and scan services, timings, and book-your-slot.",
    "cyber cafe and printing": "A printing services site with rates list, upload-order, and WhatsApp ordering.",
    "security services": "A security services site with guard/package options, B2B enquiry form, and certification trust.",
    "packers and movers": "A trust-building site with moving quotes, relocation packages, and booking form.",
    "courier service": "A courier site with tracking callbacks, delivery zones, and pickup enquiry form.",
    "laundry and dry cleaning": "A laundry site with pickup/delivery info, service menu, and order.",
    "tailor shop": "A tailor site with fitting gallery, measurement guide, and garment-order enquiry.",
    "boutique ladies tailor": "A boutique site with designer collection gallery and custom-order enquiry.",
    "embroidery unit": "A catalogue site with embroidery styles, supplier/wholesale enquiry, and unit info.",
    "ceramics and tiles unit": "A catalogue site with ceramic ranges, B2B enquiry, and bulk pricing.",
    "house cleaning service": "A cleaning service site with package tiers, hourly rates, and booking.",

    # --- Automotive ---
    "car repair garage": "A workshop site with service list, booking form, and before/after repair gallery.",
    "auto mechanic": "A mechanic site with mobile mechanic service, service list, and call-out booking.",
    "driving school": "A school site with course offerings, learner reviews, and enrolment form.",
    "e-rickshaw dealer": "A dealer site with model lineup, EMI/price enquiry, and showroom visit request.",
    "cycle shop": "A cycle shop site with models/bikes, price list, and purchase enquiry form.",
    "auto parts shop": "A parts shop site with searchable parts, fitment help, and WhatsApp order form.",
    "battery shop": "A battery & service site with size guide, exchange offers, and doorstep battery.",
    "UPS and inverter shop": "A shop site with UPS/inverter range, capacity guide, and installation request.",
    "car battery service": "A fast exit battery & site with exchange, doorstep jump-start, and booking.",

    # --- Business / professional ---
    "chartered accountant": "A professional CA site with services (GST, filing, audit), focus area list and a consult form.",
    "tax consultant": "A tax site with filing checklist, charge list, and consult-now form.",
    "auditor and accountant": "An audit firm site with audit services, team page, and enquiry form.",
    "lawyer": "A professional, trust-focused site with practice areas, credentials, and a consultation request form.",
    "real estate agent": "A conversion site with listings showcase, renewal alerts, and free valuation request.",
    "architect": "A portfolio-driven site with project gallery, design process, and project-enquiry form.",
    "property management": "A site with property listings, rental enquiry, and service forms.",
    "travel agency": "A travel site with itineraries, packages/custom trips, and free quote.",
    "signage and flex printing": "A signage shop site with material gallery, digital print quote, and price list.",
    "printing press": "A printing site with product list (cards, banners), get-a-quote form, and jobs gallery.",

    # --- Food ---
    "caterer": "A caterer site with menu, catering flavour, gallery and instant quote.",
    "bakery and cake shop": "A delicious site with cake gallery, custom cake order form and delivery areas.",
    "ice cream parlour": "A fun site with flavours/gallery, kid-friendly events corner, and store locator.",
    "cafe": "A mouth-watering menu site with coffee board, eat-out booking and timings.",

    # --- Retail / shops ---
    "jewellery shop": "A premium site with jewellery collection, custom design enquiry, and showroom visit.",
    "florist": "A blooming site with arrangement gallery, same-day delivery order and call-to-order.",
    "gifts shop": "A gifts site with categories, personalised wrapping option, and order form.",
    "stationery shop": "A stationery site with supplies list, school-price list, and order enquiry.",
    "book store": "A bookstore site with new arrivals, categories and quick order form.",
    "shoe store": "A footwear site with size guide, new arrivals and order form.",
    "clothes store": "A fashion site with collections, festive arrivals and WhatsApp order.",
    "textile shop": "A textile site with fabric range, wholesale enquiry, and price list.",
    "linen store": "A linen site with bedding range, quality notes and order enquiry.",
    "utensils store": "A utensils site with range of items, bulk rate enquiry and survey.",
    "kitchen items store": "A kitchenware site with product list, kitchen tips and order form.",
    "mattress shop": "A mattress site with firmness guide, sizes, and home trial schedule.",
    "furniture store": "A furniture showcase site with collections, price enquiry and delivery booking.",
    "home appliances store": "A store site with appliance range, price enquiry, and delivery set-up.",
    "mobile accessories shop": "An accessories site with compatible products, prices, and counter pickup or COD.",
    "bathroom fittings showroom": "A fittings showroom site with product range, installation guidance, and price list.",
    "bathroom fittings shop": "A fittings shop site with product range, installation guidance, and price enquiry.",
    "PVC furniture": "A PVC furniture info site with product images, applications, and order enquiry.",
    "modular kitchen": "A design-led site with kitchen styles, price guide, and free-site-measurement form.",
    "lighting store": "A lighting showcase with product line and order/quote.",
    "furnishing store": "A soft-furnishing site with curtains/Roman styles, price and fitting request.",
    "grocery store": "A store site with category snacks, home delivery and WhatsApp order.",
    "general store": "A simple store site with essentials list, store timings, and order.",
    "fruit and vegetable wholesale": "A B2B site with daily rates sheet, bulk order, and supply area.",
    "leather goods": "A leather-products site with collection and custom-order fun.",
    "mobile accessories": "An accessories site with product range and compatibility guide for quick orders.",

    # --- Wedding / events ---
    "event planner": "A vibrant event site with event types, past gallery, and quote form.",
    "wedding photographer": "A portfolio site with real wedding galleries, packages and booking.",
    "photographer": "A portfolio site with photography services, proof galleries and booking.",
    "tent house and decoration": "A tent-decor site with setup options, function types, and quote request.",

    # --- Education ---
    "tutoring centre": "An enrolment-friendly site with subjects, batches, and admission form.",
    "computer coaching institute": "A course site with course list, batch schedule, fees, and admission enquiry.",
    "language classes": "A classes site with course levels, demo signup and fees.",
    "training institute": "A course site with programs, batch news, and enquiry form.",

    # --- Misc local ---
    "cable TV operator": "A channel packages site with recharge, connection and promise of reliable service.",
    "cyber cafe and printing": "A printing services site with rate list, upload-order and WhatsApp ordering.",
    "courier partner service": "A pickup-and-drop site with zones, rates, and booking.",
    "small factory operator": "A catalogue site for your products, MOQ policy, and wholesale order form.",
    "garment manufacturer": "A manufacturer site with catalogue, wholesale enquiry, and MOQ info.",
    "machinery supplier": "A supplier site with machine types, price list, and sale enquiry form.",
    "pipe supplier": "A supplier site with pipe range, size/price table, and bulk-order enquiry.",
    "cement shop": "A supplier site with cement price, stock-in enquiry, and bulk request.",
    "building material supplier": "A material site with assortment, bulk enquiry, and delivery zones.",
    "lumber supplier": "A lumber site with timber grades, dimensions, and custom order delay.",
    "tile and marble supplier": "A showroom site with tile/marble catalogue, wholesale price and quote form.",
    "hardware shop": "A hardware site with product range, wholesale prices, and order.",
    "glass and mirror shop": "A shop site with glass/decor designs, custom-size enquiry and fitting service.",
    "material supply": "A supply site with product material listings and bulk order.",
}

DEFAULT_OFFER = "A modern, mobile-friendly redesign with clear services, contact info, and a simple booking/inquiry form."


def score_lead(lead, audit):
    """
    Returns an integer opportunity score (higher = better opportunity) and
    a short reason string.
    Scoring logic:
      - No website at all: highest priority (60 base)
      - Has website but missing HTTPS / mobile / old footer year: scaled by how many issues
      - Good review count = more established business = worth more to them = slightly higher score
    """
    score = 0
    reasons = []

    if not audit["has_website"]:
        score += 60
        reasons.append("no website")
    else:
        if not audit["is_https"]:
            score += 15
            reasons.append("no HTTPS")
        if not audit["has_mobile_viewport"]:
            score += 20
            reasons.append("not mobile-friendly")
        if audit.get("footer_year") and audit["footer_year"] <= 2022:
            score += 10
            reasons.append(f"outdated (footer {audit['footer_year']})")
        if not audit["load_ok"]:
            score += 10
            reasons.append("site broken/slow to load")

    # Reviews help score too
    try:
        review_count = int(lead.get("review_count") or 0)
        if review_count >= 20:
            score += 10
            reasons.append(f"{review_count} reviews — established business")
    except (ValueError, TypeError):
        pass

    reason_str = ", ".join(reasons) if reasons else "no major issues found"
    return score, reason_str


def get_offer_text(category):
    """Personalized offer line for a niche; falls back to nearest match."""
    key = (category or "").strip().lower()
    templates = {k.lower(): v for k, v in CATEGORY_OFFER_TEMPLATES.items()}
    if key in templates:
        return templates[key]
    for known, offer in templates.items():
        if key in known or known in key:
            return offer
    return DEFAULT_OFFER