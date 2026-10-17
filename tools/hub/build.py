#!/usr/bin/env python3
"""Build the ECONTEUR products hub from tools/hub/products.json.

    python3 tools/hub/build.py            # writes the site into the repo root
    python3 tools/hub/build.py --check    # validates data only

Rules baked in (owner decisions): every product says "Created and designed by
ECONTEUR LLC"; "Powered by Raimovia" appears ONLY on products whose data says
poweredByRaimovia=true (true only where it is true); store badges only for
LIVE listings; "coming" items never get an invented date; no invented numbers,
ratings or testimonials; comparison cells carry sources.
"""
import html, json, os, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(os.path.dirname(__file__), "products.json")
SITE = json.load(open(DATA))
BASE = SITE["baseUrl"].rstrip("/")          # canonical origin, e.g. https://www.econteur.com
PREFIX = SITE.get("pathPrefix", "")          # "" on econteur.com, "/econteur-apps" on GitHub Pages
TODAY = datetime.date.today().isoformat()
e = lambda s: html.escape(str(s), quote=True)

def url(path):  # absolute canonical URL for a site path like "/products/raimzeal/"
    return BASE + path

def href(path):  # link usable on whichever host serves the site
    return PREFIX + path

STATUS_LABEL = {"live": "Live", "review": "In review", "soon": "Coming soon", "testflight": "Beta", "web": "Live on the web"}

def pill(platform, st):
    cls = {"live": "live", "web": "live", "review": "review", "testflight": "review"}.get(st, "soon")
    return f'<span class="pill {cls}">{e(platform)} · {e(STATUS_LABEL.get(st, st))}</span>'

def icon(p, cls="icon"):
    if p.get("icon"):
        return f'<img class="{cls}" src="{e(href(p["icon"]))}" alt="" width="96" height="96" loading="lazy" decoding="async">'
    return f'<span class="{cls} ph" aria-hidden="true">{e(p["name"][0])}</span>'

def head(title, desc, path, extra_ld=(), og_image=None):
    ld = [SITE_LD] + list(extra_ld)
    og = og_image or SITE.get("ogImage")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url(path))}">
<meta name="theme-color" content="#0d0b14" media="(prefers-color-scheme: dark)"><meta name="theme-color" content="#f7f6fb" media="(prefers-color-scheme: light)">
<meta property="og:type" content="website"><meta property="og:site_name" content="ECONTEUR LLC">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(url(path))}">
{f'<meta property="og:image" content="{e(url(og))}">' if og else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{href('/assets/hub.css')}">
<link rel="icon" href="{href('/assets/favicon.svg')}" type="image/svg+xml">
{''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)}
</head><body>
<a class="skip" href="#main">Skip to content</a>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="grain" aria-hidden="true"></div>
<header class="top"><div class="wrap">
<a class="brand" href="{href('/')}" aria-label="ECONTEUR home"><b>E</b>ECONTEUR</a>
<nav aria-label="Main">
<a href="{href('/#products')}">Products</a>
<a class="opt" href="{href('/compare/')}">Compare</a>
<a class="opt" href="{href('/roadmap/')}">Coming next</a>
<a href="{href('/#faq')}">FAQ</a>
</nav></div></header>
<main id="main">"""

def foot():
    prods = "".join(f'<a href="{href("/products/" + p["slug"] + "/")}">{e(p["name"])}</a>' for p in SITE["products"] if not p.get("hidden"))
    return f"""</main>
<footer class="site"><div class="wrap">
<div class="cols">
<div><h4>Products</h4>{prods}</div>
<div><h4>Company</h4><a href="{href('/#about')}">About ECONTEUR</a><a href="{href('/roadmap/')}">Coming next</a><a href="{href('/compare/')}">Compare</a><a href="{href('/legal/')}">Privacy, terms &amp; support</a></div>
<div><h4>Contact</h4><a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a></div>
</div>
<p class="made">Every product here is <strong>created and designed by ECONTEUR LLC</strong>{e(SITE.get('since',''))}. Founded by {e(SITE['founder'])}.</p>
<p class="made">© {datetime.date.today().year} ECONTEUR LLC. App Store is a service mark of Apple Inc. Google Play is a trademark of Google LLC. Competitor names belong to their owners and are used only to compare publicly available information.</p>
</div></footer>
<script src="{href('/assets/hub.js')}" defer></script>
</body></html>
"""

SITE_LD = {
    "@context": "https://schema.org", "@type": "Organization", "name": "ECONTEUR LLC",
    "url": BASE + "/", "email": SITE["email"], "foundingDate": SITE.get("foundingDate"),
    "founder": {"@type": "Person", "name": SITE["founder"]},
    "logo": url(SITE["logo"]) if SITE.get("logo") else None,
}
SITE_LD = {k: v for k, v in SITE_LD.items() if v}

def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in items]}

def crumbs_ld(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": url(p)} for i, (n, p) in enumerate(trail)]}

def app_ld(p):
    os_ = ", ".join(sorted({k for k, v in p["status"].items() if v in ("live", "review", "testflight", "web")})) or None
    d = {"@context": "https://schema.org", "@type": "SoftwareApplication" if p.get("kind") != "game" else "VideoGame",
         "name": p["name"], "description": p["summary"], "applicationCategory": p.get("schemaCategory", "Application"),
         "operatingSystem": os_, "url": url(f'/products/{p["slug"]}/'),
         "author": {"@type": "Organization", "name": "ECONTEUR LLC"}, "creator": {"@type": "Organization", "name": "ECONTEUR LLC"}}
    if p.get("offers"):
        d["offers"] = p["offers"]
    if p.get("icon"):
        d["image"] = url(p["icon"])
    return {k: v for k, v in d.items() if v}

def card(p):
    pills = "".join(pill(k, v) for k, v in p["status"].items())
    return f"""<article class="card reveal" data-cat="{e(' '.join(p['filters']))}"><span class="glare"></span>
<div class="card-top">{icon(p)}<div><div class="cat">{e(p['category'])}</div><h3>{e(p['name'])}</h3></div></div>
<p>{e(p['tagline'])}</p>
<div class="status">{pills}</div>
<a class="more stretch" href="{href('/products/' + p['slug'] + '/')}">See {e(p['name'])}</a>
</article>"""

def get_buttons(p):
    out = []
    for g in p.get("get", []):
        out.append(f'<a class="btn {"primary" if not out else "ghost"}" href="{e(g["url"])}" rel="noopener">{e(g["label"])}</a>')
    return "".join(out) or '<span class="pill soon">Not available to download yet — see status below</span>'

def comparison(p):
    c = p.get("compare")
    if not c:
        return ""
    cols = c["competitors"]
    headrow = '<th scope="col">Feature</th>' + f'<th scope="col" class="us">{e(p["name"])}</th>' + "".join(f'<th scope="col">{e(x)}</th>' for x in cols)
    sym = {"y": ('<span class="y" aria-label="Yes">✓</span>'), "n": ('<span class="n" aria-label="No">✗</span>'), "p": ('<span class="p" aria-label="Partly">◐</span>')}
    def cell(v, us=False):
        cls = ' class="us"' if us else ""
        if v in sym: return f"<td{cls}>{sym[v]}</td>"
        return f"<td{cls}>{e(v)}</td>"
    rows = "".join("<tr><th scope=\"row\">" + e(r["feature"]) + "</th>" + cell(r["us"], True) + "".join(cell(v) for v in r["them"]) + "</tr>" for r in c["rows"])
    srcs = " · ".join(f'<a href="{e(s["url"])}" rel="nofollow noopener">{e(s["name"])}</a>' for s in c.get("sources", []))
    adv = "".join(f"<li><strong>{e(a['t'])}</strong><span>{e(a['d'])}</span></li>" for a in c.get("advantages", []))
    honest = "".join(f"<li><strong>{e(a['t'])}</strong><span>{e(a['d'])}</span></li>" for a in c.get("honest", []))
    return f"""<section id="compare"><div class="sec-head reveal"><div><h2>{e(p['name'])} vs the top alternatives</h2>
<p>Side by side with the {len(cols)} best-known alternatives, from their public pages ({e(c.get('checked', TODAY))}). ✓ yes · ◐ partly · ✗ no.</p></div></div>
<div class="tbl-wrap reveal"><table><caption class="skip">{e(p['name'])} compared with {e(', '.join(cols))}</caption><thead><tr>{headrow}</tr></thead><tbody>{rows}</tbody></table></div>
<p class="src">Sources: {srcs or 'each company’s public site'}. Prices and features change — check each company’s site before you buy. Spotted something out of date? Email {e(SITE['email'])}.</p>
{f'<h3 style="margin:30px 0 12px">Where {e(p["name"])} wins</h3><ul class="feat">{adv}</ul>' if adv else ''}
{f'<h3 style="margin:26px 0 12px">Where others are stronger (honestly)</h3><ul class="feat">{honest}</ul>' if honest else ''}
</section>"""

def product_page(p):
    path = f'/products/{p["slug"]}/'
    feats = "".join(f"<li><strong>{e(f['t'])}</strong><span>{e(f['d'])}</span></li>" for f in p["features"])
    coming = "".join(f"<li><strong>{e(f['t'])}</strong><span>{e(f.get('d',''))} — {e(f.get('when','date not set'))}</span></li>" for f in p.get("coming", []))
    notes = "".join(f'<p class="note">{e(n)}</p>' for n in p.get("notes", []))
    faq = p.get("faq", [])
    faq_html = "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in faq)
    powered = '<p class="made" style="margin-top:14px">Runs on the <strong>Raimovia</strong> platform.</p>' if p.get("poweredByRaimovia") else ""
    pills = "".join(pill(k, v) for k, v in p["status"].items())
    trail = [("ECONTEUR", "/"), ("Products", "/#products"), (p["name"], path)]
    ld = [app_ld(p), crumbs_ld(trail)] + ([faq_ld(faq)] if faq else [])
    body = f"""<div class="wrap">
<section class="p-hero"><nav class="crumbs" aria-label="Breadcrumb"><a href="{href('/')}">ECONTEUR</a> / <a href="{href('/#products')}">Products</a> / {e(p['name'])}</nav>
<div class="row">{icon(p)}<div><div class="cat">{e(p['category'])}</div><h1>{e(p['name'])}</h1></div></div>
<p class="lede" style="margin:18px 0 0;text-align:left">{e(p['summary'])}</p>
<div class="status" style="margin-top:18px">{pills}</div>
<div class="get">{get_buttons(p)}</div>
<p class="made" style="margin-top:16px">Created and designed by <strong>ECONTEUR LLC</strong>.</p>{powered}
</section>
<section><div class="sec-head reveal"><div><h2>What it does</h2><p>{e(p.get('who',''))}</p></div></div><ul class="feat">{feats}</ul>{notes and f'<div style="margin-top:18px;display:grid;gap:10px">{notes}</div>'}</section>
{f'<section><div class="sec-head reveal"><div><h2>Coming next</h2><p>What we are building for {e(p["name"])}. No dates until we are sure.</p></div></div><ul class="feat">{coming}</ul></section>' if coming else ''}
<section><div class="sec-head reveal"><div><h2>How to get {e(p['name'])}</h2></div></div><ol class="feat" style="padding:0">{''.join(f'<li><strong>Step {i+1}</strong><span>{e(s)}</span></li>' for i, s in enumerate(p.get('howto', [])))}</ol></section>
{comparison(p)}
{f'<section class="faq" id="faq"><div class="sec-head reveal"><div><h2>Questions about {e(p["name"])}</h2></div></div>{faq_html}</section>' if faq_html else ''}
</div>"""
    write(path, head(p["seoTitle"], p["seoDescription"], path, ld, p.get("icon")) + body + foot())

def home():
    ps = [p for p in SITE["products"] if not p.get("hidden")]
    cats = []
    for p in ps:
        for f in p["filters"]:
            if f not in cats: cats.append(f)
    chips = '<button class="chip" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" data-filter="{e(c)}" aria-pressed="false">{e(SITE["filterNames"].get(c, c))}</button>' for c in cats)
    facts = "".join(f'<div class="fact reveal"><strong data-count="{e(f["n"])}" data-suffix="{e(f.get("suffix",""))}">{e(f["n"])}{e(f.get("suffix",""))}</strong><span>{e(f["label"])}</span></div>' for f in SITE["facts"])
    values = "".join(f'<div class="value reveal"><div class="ico" aria-hidden="true">{v["icon"]}</div><h3>{e(v["t"])}</h3><p>{e(v["d"])}</p></div>' for v in SITE["values"])
    faq = SITE["faq"]
    faq_html = "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in faq)
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "name": "Products by ECONTEUR LLC",
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": url(f'/products/{p["slug"]}/'), "name": p["name"]} for i, p in enumerate(ps)]}
    body = f"""<div class="wrap">
<section class="hero"><span class="eyebrow"><span class="dot" aria-hidden="true"></span>{e(SITE['heroEyebrow'])}</span>
<h1>{SITE['heroTitleHtml']}</h1>
<p class="lede">{e(SITE['heroLede'])}</p>
<div class="cta-row"><a class="btn primary" href="#products">Explore the products</a><a class="btn ghost" href="{href('/roadmap/')}">See what’s coming</a></div>
<div class="facts">{facts}</div></section>
<section id="products"><div class="sec-head"><div><h2>One maker. Every tool you need.</h2><p>{e(SITE['productsLede'])}</p></div>
<div class="chips" role="group" aria-label="Filter products">{chips}</div></div>
<p id="filter-status" class="skip" aria-live="polite"></p>
<div class="grid">{''.join(card(p) for p in ps)}</div></section>
<section id="about"><div class="sec-head reveal"><div><h2>{e(SITE['aboutTitle'])}</h2><p>{e(SITE['aboutText'])}</p></div></div><div class="values">{values}</div></section>
<section class="faq" id="faq"><div class="sec-head reveal"><div><h2>Questions people ask</h2></div></div>{faq_html}</section>
</div>"""
    write("/", head(SITE["seoTitle"], SITE["seoDescription"], "/", [itemlist, faq_ld(faq)]) + body + foot())

def compare_index():
    ps = [p for p in SITE["products"] if p.get("compare") and not p.get("hidden")]
    cards = "".join(f'<article class="card reveal"><span class="glare"></span><div class="card-top">{icon(p)}<div><div class="cat">{e(p["category"])}</div><h3>{e(p["name"])} vs {e(", ".join(p["compare"]["competitors"][:3]))} +{max(0,len(p["compare"]["competitors"])-3)}</h3></div></div><p>{e(p["compare"].get("blurb", p["tagline"]))}</p><a class="more stretch" href="{href("/products/" + p["slug"] + "/#compare")}">See the comparison</a></article>' for p in ps)
    body = f"""<div class="wrap"><section class="hero" style="padding-bottom:10px"><h1>Compare <span class="grad">honestly</span></h1><p class="lede">Each ECONTEUR product next to the best-known alternatives — what each one does, what it costs, and where others are stronger.</p></section>
<section><div class="grid">{cards}</div></section></div>"""
    write("/compare/", head("Compare ECONTEUR apps with the alternatives | ECONTEUR LLC", "Honest side-by-side comparisons of RAIMZEAL, V3EDGE, RaimCalls, Raimovia and more with their top competitors: features, prices and free plans.", "/compare/", [crumbs_ld([("ECONTEUR", "/"), ("Compare", "/compare/")])]) + body + foot())

def roadmap():
    items = []
    for p in SITE["products"]:
        if p.get("hidden"): continue
        for k, v in p["status"].items():
            if v in ("review", "soon", "testflight"):
                items.append((p, f'{k}: {STATUS_LABEL.get(v, v)}', p.get("statusNote", {}).get(k, "")))
        for c in p.get("coming", []):
            items.append((p, c["t"], c.get("when", "Date not set")))
    rows = "".join(f'<div class="item reveal">{icon(p)}<div><div class="cat">{e(p["name"])}</div><strong>{e(what)}</strong><div style="color:var(--muted);font-size:15px">{e(when)}</div></div></div>' for p, what, when in items)
    body = f"""<div class="wrap"><section class="hero" style="padding-bottom:10px"><h1>What’s <span class="grad">coming next</span></h1><p class="lede">{e(SITE['roadmapLede'])}</p></section><section><div class="road">{rows}</div></section></div>"""
    write("/roadmap/", head("Coming soon from ECONTEUR LLC — apps in review and new features", "What ECONTEUR LLC is releasing next: apps in App Store and Google Play review, upcoming features and new products. No invented dates.", "/roadmap/", [crumbs_ld([("ECONTEUR", "/"), ("Coming next", "/roadmap/")])]) + body + foot())

def legal():
    rows = "".join(f'<li><strong>{e(l["name"])}</strong><span>' + " · ".join(f'<a href="{href(x["path"])}">{e(x["label"])}</a>' for x in l["links"]) + "</span></li>" for l in SITE["legal"])
    body = f"""<div class="wrap"><section class="p-hero"><h1>Privacy, terms &amp; support</h1><p class="lede" style="text-align:left;margin:14px 0 0">Legal and support pages for apps published by ECONTEUR LLC. Questions: <a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a>.</p></section><section><ul class="feat">{rows}</ul></section></div>"""
    write("/legal/", head("Privacy, terms & support — ECONTEUR LLC apps", "Privacy policies, terms of use, support and data deletion for every app made by ECONTEUR LLC.", "/legal/") + body + foot())

def seo_files():
    paths = ["/", "/compare/", "/roadmap/", "/legal/"] + [f'/products/{p["slug"]}/' for p in SITE["products"] if not p.get("hidden")]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{e(url(p))}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in paths) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {url('/sitemap.xml')}\n")
    lines = [f"# ECONTEUR LLC", "", f"> {SITE['seoDescription']}", "", f"Founder: {SITE['founder']}. Contact: {SITE['email']}.", "", "## Products"]
    for p in SITE["products"]:
        if p.get("hidden"): continue
        st = ", ".join(f"{k} {STATUS_LABEL.get(v, v).lower()}" for k, v in p["status"].items())
        lines.append(f"- [{p['name']}]({url('/products/' + p['slug'] + '/')}): {p['summary']} Status: {st}.")
    lines += ["", "## Notes", "- Every product is created and designed by ECONTEUR LLC.", "- ECONTEUR products do not use Chinese AI models."] + [f"- {n}" for n in SITE.get("llmsNotes", [])]
    open(os.path.join(ROOT, "llms.txt"), "w").write("\n".join(lines) + "\n")

def write(path, doc):
    out = os.path.join(ROOT, path.strip("/"), "index.html") if path != "/" else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

def check():
    errs = []
    for p in SITE["products"]:
        for k in ("slug", "name", "category", "tagline", "summary", "features", "status", "filters", "seoTitle", "seoDescription"):
            if not p.get(k): errs.append(f"{p.get('slug')}: missing {k}")
        if len(p.get("seoTitle", "")) > 65: errs.append(f"{p['slug']}: seoTitle {len(p['seoTitle'])} > 65")
        if not 70 <= len(p.get("seoDescription", "")) <= 160: errs.append(f"{p['slug']}: seoDescription {len(p.get('seoDescription',''))} not 70-160")
        for g in p.get("get", []):
            plat = g.get("platform")
            if plat and p["status"].get(plat) not in ("live", "web"):
                errs.append(f"{p['slug']}: store button for {plat} but status is {p['status'].get(plat)}")
        c = p.get("compare")
        if c:
            n = len(c["competitors"])
            for r in c["rows"]:
                if len(r["them"]) != n: errs.append(f"{p['slug']}: row '{r['feature']}' has {len(r['them'])} cells, expected {n}")
        if p.get("poweredByRaimovia") and p["slug"] != "raimcalls":
            errs.append(f"{p['slug']}: poweredByRaimovia is only true for RaimCalls")
        text = json.dumps(p).lower()
        for bad in ("dr. oviawe\"", " md ", "physician", "501(c)(3) charity", "tax-deductible\""):
            if bad in text: errs.append(f"{p['slug']}: forbidden wording '{bad}'")
    return errs

if __name__ == "__main__":
    errs = check()
    if errs:
        print("\n".join(errs)); sys.exit(1)
    if "--check" in sys.argv:
        print("data ok"); sys.exit(0)
    home(); compare_index(); roadmap(); legal(); seo_files()
    for p in SITE["products"]:
        if not p.get("hidden"): product_page(p)
    print(f"built {len([p for p in SITE['products'] if not p.get('hidden')])} product pages + home, compare, roadmap, legal, sitemap, robots, llms.txt")
