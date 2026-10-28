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

def ld_json(x):  # JSON-LD that can never close its own <script> tag
    return json.dumps(x, ensure_ascii=False).replace("</", "<\\/")

def head(title, desc, path, extra_ld=(), og_image=None, og=None, extra_head="", canonical=None):
    """og = {"path","width","height","alt"} for a real 1200x630 share image; og_image = legacy icon path."""
    ld = [SITE_LD] + list(extra_ld)
    canon = url(canonical or path)
    og = og or ({"path": og_image or SITE.get("ogImage")} if (og_image or SITE.get("ogImage")) else None)
    og_tags = ""
    if og:
        og_tags = f'<meta property="og:image" content="{e(url(og["path"]))}">'
        if og.get("width"): og_tags += f'<meta property="og:image:width" content="{og["width"]}"><meta property="og:image:height" content="{og["height"]}">'
        if og.get("alt"): og_tags += f'<meta property="og:image:alt" content="{e(og["alt"])}"><meta name="twitter:image:alt" content="{e(og["alt"])}">'
        og_tags += f'<meta name="twitter:image" content="{e(url(og["path"]))}">'
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canon)}">
<meta name="theme-color" content="#0d0b14" media="(prefers-color-scheme: dark)"><meta name="theme-color" content="#f7f6fb" media="(prefers-color-scheme: light)">
<meta property="og:type" content="website"><meta property="og:site_name" content="ECONTEUR LLC">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon)}">
{og_tags}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">{extra_head}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{href('/assets/hub.css')}">
<link rel="icon" href="{href('/assets/favicon.svg')}" type="image/svg+xml">
{''.join(f'<script type="application/ld+json">{ld_json(x)}</script>' for x in ld)}
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

def page_path(p):  # the product's canonical page (its own official page when it has one)
    return p.get("canonical") or f'/products/{p["slug"]}/'

def foot():
    prods = "".join(f'<a href="{href(page_path(p))}">{e(p["name"])}</a>' for p in SITE["products"] if not p.get("hidden"))
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
         "operatingSystem": os_, "url": url(page_path(p)),
         "author": {"@type": "Organization", "name": "ECONTEUR LLC"}, "creator": {"@type": "Organization", "name": "ECONTEUR LLC"}}
    if p.get("offers"):
        d["offers"] = p["offers"]
    if p.get("icon"):
        d["image"] = url(p["icon"])
    lp = p.get("landing") or {}
    if lp.get("hero"):
        d["image"] = [url(lp["hero"]["jpg"])] + ([url(lp["og"]["path"])] if lp.get("og") else [])
    d.update(p.get("ld", {}))   # alternateName, sameAs, author, publisher… — must match the visible page
    return {k: v for k, v in d.items() if v}

def card(p):
    pills = "".join(pill(k, v) for k, v in p["status"].items())
    return f"""<article class="card reveal" data-cat="{e(' '.join(p['filters']))}"><span class="glare"></span>
<div class="card-top">{icon(p)}<div><div class="cat">{e(p['category'])}</div><h3>{e(p['name'])}</h3></div></div>
<p>{e(p['tagline'])}</p>
<div class="status">{pills}</div>
<a class="more stretch" href="{href(page_path(p))}">See {e(p['name'])}</a>
</article>"""

def get_buttons(p):
    out = []
    for g in p.get("get", []):
        out.append(f'<a class="btn {"primary" if not out else "ghost"}" href="{e(g["url"])}" rel="noopener">{e(g["label"])}</a>')
    return "".join(out) or '<span class="pill soon">Not available to download yet — see status below</span>'

SYM = {"y": '<span class="y" aria-label="Yes">✓</span>', "n": '<span class="n" aria-label="No">✗</span>', "p": '<span class="p" aria-label="Partly">◐</span>'}

def compare_table(p):
    """Table + numbered sources. Rows may carry usSrc/themSrc ids into compare.sourceMap: every cell then links
    to the page it came from. Returns (table_html, sources_html)."""
    c = p["compare"]; cols = c["competitors"]; smap = c.get("sourceMap", {}); order = []
    def ref(sid):
        if not sid or sid not in smap: return ""
        if sid not in order: order.append(sid)
        n = order.index(sid) + 1
        return f'<sup><a href="#src-{n}" aria-label="Source {n}">[{n}]</a></sup>'
    def cell(v, sid=None, us=False):
        cls = ' class="us"' if us else ""
        body = SYM.get(v) or e(v)
        return f"<td{cls}>{body}{ref(sid) if v != '—' else ''}</td>"
    headrow = '<th scope="col">Feature</th>' + f'<th scope="col" class="us">{e(p["name"])}</th>' + "".join(f'<th scope="col">{e(x)}</th>' for x in cols)
    rows = ""
    for r in c["rows"]:
        srcs = r.get("themSrc") or [None] * len(cols)
        rows += "<tr><th scope=\"row\">" + e(r["feature"]) + "</th>" + cell(r["us"], r.get("usSrc"), True) + "".join(cell(v, sid) for v, sid in zip(r["them"], srcs)) + "</tr>"
    table = f'<div class="tbl-wrap reveal" tabindex="0" role="region" aria-label="{e(p["name"])} comparison table"><table><caption class="vh">{e(p["name"])} compared with {e(", ".join(cols))}</caption><thead><tr>{headrow}</tr></thead><tbody>{rows}</tbody></table></div>'
    if order:
        lis = "".join(f'<li id="src-{i+1}"><a href="{e(smap[sid]["url"])}" rel="nofollow noopener">{e(smap[sid]["name"])}</a></li>' for i, sid in enumerate(order))
        srcs = f'<ol class="src srclist">{lis}</ol>'
    else:
        srcs = " · ".join(f'<a href="{e(s["url"])}" rel="nofollow noopener">{e(s["name"])}</a>' for s in c.get("sources", []))
        srcs = f'<p class="src">Sources: {srcs or "each company’s public site"}.</p>'
    return table, srcs

def wins_lists(p):
    c = p["compare"]
    adv = "".join(f"<li><strong>{e(a['t'])}</strong><span>{e(a['d'])}</span></li>" for a in c.get("advantages", []))
    honest = "".join(f"<li><strong>{e(a['t'])}</strong><span>{e(a['d'])}</span></li>" for a in c.get("honest", []))
    return (f'<h3 style="margin:30px 0 12px">Where {e(p["name"])} stands out</h3><ul class="feat">{adv}</ul>' if adv else '') + \
           (f'<h3 style="margin:26px 0 12px">Where others are stronger (honestly)</h3><ul class="feat">{honest}</ul>' if honest else '')

def comparison(p):
    c = p.get("compare")
    if not c:
        return ""
    cols = c["competitors"]
    table, srcs = compare_table(p)
    full = (p.get("landing") or {}).get("comparePath")
    more = f'<p style="margin-top:14px"><a class="btn ghost" href="{href(full)}">See the full comparison with every source</a></p>' if full else ""
    return f"""<section id="compare"><div class="sec-head reveal"><div><h2>{e(p['name'])} vs the top alternatives</h2>
<p>Side by side with {len(cols)} well-known alternatives, from their public pages (checked {e(c.get('checked', TODAY))}). ✓ yes · ◐ partly · ✗ no · — not verified.</p></div></div>
{table}
<p class="src">Prices and features change — check each company’s page before you buy. Spotted something out of date? Email {e(SITE['email'])}. Names and trademarks belong to their owners.</p>
{srcs}{more}
{wins_lists(p)}
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
    lp = p.get("landing") or {}
    write(path, head(p["seoTitle"], p["seoDescription"], path, ld, p.get("icon"), og=lp.get("og"), canonical=p.get("canonical")) + body + foot())

def picture(img, cls=""):  # WebP with JPG fallback; always above the fold where used, so load it first
    c = f' class="{cls}"' if cls else ""
    return (f'<picture><source type="image/webp" srcset="{href(img["webp"])}">'
            f'<img{c} src="{href(img["jpg"])}" width="{img["width"]}" height="{img["height"]}" alt="{e(img["alt"])}" decoding="async" fetchpriority="high"></picture>')

def faq_section(p, title=None):
    faq = p.get("faq", [])
    items = "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in faq)
    return f'<section class="faq" id="faq"><div class="sec-head reveal"><div><h2>{e(title or "Questions about " + p["name"])}</h2></div></div>{items}</section>' if items else ""

def game_landing(p):
    """The game's own official page (e.g. /raimaction/) and its sourced comparison page, from the same data as the hub."""
    lp = p["landing"]; path = lp["path"]; cp = lp.get("comparePath"); name = p["name"]
    feats = "".join(f"<li><strong>{e(f['t'])}</strong><span>{e(f['d'])}</span></li>" for f in p["features"])
    notes = "".join(f'<p class="note">{e(n)}</p>' for n in p.get("notes", []))
    pills = "".join(pill(k, v) for k, v in p["status"].items())
    steps = "".join(f'<li><strong>Step {i+1}</strong><span>{e(s)}</span></li>' for i, s in enumerate(p.get("howto", [])))
    legal = " · ".join(f'<a href="{href(u)}">{e(t)}</a>' for t, u in lp.get("legal", []))
    store_meta = f'<meta name="apple-itunes-app" content="app-id={e(lp["appStoreId"])}">' if lp.get("appStoreId") else ""
    adv = "".join(f"<li><strong>{e(a['t'])}</strong><span>{e(a['d'])}</span></li>" for a in (p.get("compare") or {}).get("advantages", []))
    n_comp = len((p.get("compare") or {}).get("competitors", []))
    compare_teaser = f"""<section id="compare"><div class="sec-head reveal"><div><h2>{e(name)} next to {n_comp} top mobile action games</h2>
<p>Compared on things you can check yourself (price model, ads, random-item purchases, offline play, team play and controllers), with a source for every cell.</p></div></div>
<ul class="feat">{adv}</ul>
<p style="margin-top:18px"><a class="btn primary" href="{href(cp)}">See the full comparison</a></p></section>""" if cp and adv else ""
    donate = f"""<section><div class="sec-head reveal"><div><h2>Support the Foundation</h2>
<p>{e(name)}'s free operations are sponsored by RAIMZEAL Health Foundation, Inc. Donations go to RAIMZEAL Health Foundation, Inc., a 501(c)(3) public charity (IRS determination effective August 21, 2026), and are tax-deductible to the extent allowed by law.</p></div></div>
<p><a class="btn ghost" href="{e(lp["donate"])}" rel="noopener">Donate to RAIMZEAL Health Foundation</a></p></section>""" if lp.get("donate") else ""
    body = f"""<div class="wrap">
<section class="game-hero">
<div><nav class="crumbs" aria-label="Breadcrumb"><a href="{href('/')}">ECONTEUR</a> / {e(name)}</nav>
<span class="eyebrow"><span class="dot" aria-hidden="true"></span>{e(p['category'])} · iPhone · iPad · Android</span>
<h1>{e(name)}</h1>
<p class="lede" style="margin:0;text-align:left">{e(lp.get('lede') or p['summary'])}</p>
<p class="purpose">{e(lp.get('purpose', ''))}</p>
<div class="status" style="margin-top:18px">{pills}</div>
<div class="get">{get_buttons(p)}</div>
<p class="made" style="margin-top:16px">Created and designed by <strong>ECONTEUR LLC</strong>. Free operations sponsored by <strong>RAIMZEAL Health Foundation, Inc.</strong></p>
<p class="aka">{e(lp.get('searchNames', ''))}</p></div>
<figure>{picture(lp['hero'])}<figcaption>{e(lp.get('operatorsLine', ''))}</figcaption></figure>
</section>
<section><div class="sec-head reveal"><div><h2>What's inside {e(name)}</h2><p>{e(p.get('who', ''))}</p></div></div><ul class="feat">{feats}</ul></section>
<section><div class="sec-head reveal"><div><h2>Free forever, Premium when you want more</h2><p>Free operations: {e(', '.join(lp.get('freeOps', [])))}. Plus one Premium operation free to play each week.</p></div></div><div style="display:grid;gap:10px">{notes}</div></section>
<section><div class="sec-head reveal"><div><h2>How to start</h2></div></div><ol class="feat" style="padding:0">{steps}</ol></section>
{compare_teaser}
{faq_section(p)}
{donate}
<section><div class="sec-head reveal"><div><h2>Privacy, terms &amp; support</h2><p>{legal}. Contact: <a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a>.</p></div></div></section>
</div>"""
    ld = [app_ld(p), crumbs_ld([("ECONTEUR", "/"), (name, path)])] + ([faq_ld(p["faq"])] if p.get("faq") else [])
    write(path, head(lp["title"], lp["description"], path, ld, og=lp.get("og"), extra_head=store_meta) + body + foot())
    if not cp or not p.get("compare"):
        return
    c = p["compare"]
    table, srcs = compare_table(p)
    cbody = f"""<div class="wrap">
<section class="p-hero"><nav class="crumbs" aria-label="Breadcrumb"><a href="{href('/')}">ECONTEUR</a> / <a href="{href(path)}">{e(name)}</a> / Compare</nav>
<div class="cmp-head">{picture(lp["hero"], "cmp-img")}<div><div class="cat">Comparison · checked {e(c.get('checked', TODAY))}</div>
<h1>{e(name)} vs the top {len(c['competitors'])} mobile action games</h1>
<p class="lede" style="margin:14px 0 0;text-align:left">How {e(name)} compares with {e(', '.join(c['competitors'][:-1]))} and {e(c['competitors'][-1])}, on things you can check yourself.</p></div></div>
<div class="get">{get_buttons(p)}<a class="btn ghost" href="{href(path)}">About {e(name)}</a></div>
</section>
<section><p class="note">{e(c.get('method', ''))}</p></section>
<section style="padding-top:0">{table}
<p class="src">Prices and features change — check each publisher's page before you buy. Spotted something out of date? Email {e(SITE['email'])}. Game names and trademarks belong to their owners and are used only to compare publicly available information.</p>
<h2 style="margin:34px 0 10px;font-size:1.4rem">Sources</h2>{srcs}
{wins_lists(p)}
</section>
{faq_section(p)}
</div>"""
    cld = [crumbs_ld([("ECONTEUR", "/"), (name, path), ("Compare", cp)])]
    write_file(cp, head(lp["compareTitle"], lp["compareDescription"], cp, cld, og=lp.get("og")) + cbody + foot())

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
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": url(page_path(p)), "name": p["name"]} for i, p in enumerate(ps)]}
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
    cards = "".join(f'<article class="card reveal"><span class="glare"></span><div class="card-top">{icon(p)}<div><div class="cat">{e(p["category"])}</div><h3>{e(p["name"])} vs {e(", ".join(p["compare"]["competitors"][:3]))} +{max(0,len(p["compare"]["competitors"])-3)}</h3></div></div><p>{e(p["compare"].get("blurb", p["tagline"]))}</p><a class="more stretch" href="{href((p.get("landing") or {}).get("comparePath") or "/products/" + p["slug"] + "/#compare")}">See the comparison</a></article>' for p in ps)
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

AI_AND_SEARCH_BOTS = ["Googlebot", "Google-Extended", "Bingbot", "Applebot", "Applebot-Extended", "DuckDuckBot", "DuckAssistBot",
    "YandexBot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "anthropic-ai",
    "PerplexityBot", "Perplexity-User", "Amazonbot", "meta-externalagent", "CCBot", "cohere-ai", "MistralAI-User"]

def seo_files():
    ps = [p for p in SITE["products"] if not p.get("hidden")]
    paths = ["/", "/compare/", "/roadmap/", "/legal/"] + [page_path(p) for p in ps] + \
            [p["landing"]["comparePath"] for p in ps if (p.get("landing") or {}).get("comparePath")]
    imgs = {p["landing"]["path"]: p["landing"]["hero"] for p in ps if (p.get("landing") or {}).get("hero")}
    def entry(pth):
        im = imgs.get(pth)
        x = f"<image:image><image:loc>{e(url(im['jpg']))}</image:loc></image:image>" if im else ""
        return f"<url><loc>{e(url(pth))}</loc><lastmod>{TODAY}</lastmod>{x}</url>\n"
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "".join(entry(p) for p in paths) + "</urlset>\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)
    robots = ["User-agent: *", "Allow: /", "", "# Search engines and AI assistants are welcome to read and cite every page."]
    robots += [f"User-agent: {b}" for b in AI_AND_SEARCH_BOTS] + ["Allow: /", "", f"Sitemap: {url('/sitemap.xml')}"]
    open(os.path.join(ROOT, "robots.txt"), "w").write("\n".join(robots) + "\n")
    lines = [f"# ECONTEUR LLC", "", f"> {SITE['seoDescription']}", "", f"Founder: {SITE['founder']}. Contact: {SITE['email']}.", "", "## Products"]
    for p in ps:
        st = ", ".join(f"{k} {STATUS_LABEL.get(v, v).lower()}" for k, v in p["status"].items())
        lines.append(f"- [{p['name']}]({url(page_path(p))}): {p['summary']} Status: {st}.")
    for p in ps:
        lp = p.get("landing")
        if not lp: continue
        lines += ["", f"## {p['name']} — key facts", f"- Official page: {url(lp['path'])}"]
        if lp.get("comparePath"): lines.append(f"- Sourced comparison with {len(p['compare']['competitors'])} mobile action games: {url(lp['comparePath'])}")
        lines += [f"- {g['label']}: {g['url']}" for g in p.get("get", [])]
        lines.append(f"- Full facts for AI assistants: {url(lp['path'] + 'llms.txt')}")
        lines += [f"- {f['t']}: {f['d']}" for f in p["features"]] + [f"- {n}" for n in p.get("notes", [])]
        if p.get("ld", {}).get("alternateName"): lines.append(f"- Also written: {', '.join(p['ld']['alternateName'])}. {lp.get('searchNames', '')}")
        game_llms(p)
    lines += ["", "## Notes", "- Every product is created and designed by ECONTEUR LLC.", "- ECONTEUR products do not use Chinese AI models."] + [f"- {n}" for n in SITE.get("llmsNotes", [])]
    open(os.path.join(ROOT, "llms.txt"), "w").write("\n".join(lines) + "\n")

def game_llms(p):
    """/<game>/llms.txt: every verified fact, the FAQ and the sourced comparison as plain markdown."""
    lp = p["landing"]; c = p.get("compare") or {}
    L = [f"# {p['name']}", "", f"> {p['summary']}", "", lp.get("purpose", ""), "",
         f"Official page: {url(lp['path'])}", f"Made by: ECONTEUR LLC (founder Dr. Ephraim Oviawe, who performs as RAIMZY). Contact: {SITE['email']}."]
    L += [f"{g['label']}: {g['url']}" for g in p.get("get", [])]
    L += ["", "## Facts"] + [f"- {f['t']}: {f['d']}" for f in p["features"]] + [f"- {n}" for n in p.get("notes", [])]
    L += [f"- {lp.get('operatorsLine', '')}", f"- {lp.get('searchNames', '')}", "- Prices are not listed here because they vary by country; the app shows them."]
    L += ["", "## How to start"] + [f"{i+1}. {s}" for i, s in enumerate(p.get("howto", []))]
    L += ["", "## FAQ"] + sum(([f"### {q['q']}", q["a"], ""] for q in p.get("faq", [])), [])
    if c:
        smap = c.get("sourceMap", {})
        L += [f"## Comparison with {len(c['competitors'])} mobile action games (checked {c.get('checked')})", "", c.get("method", ""), ""]
        L.append("| Feature | " + p["name"] + " | " + " | ".join(c["competitors"]) + " |")
        L.append("|" + "---|" * (len(c["competitors"]) + 2))
        for r in c["rows"]:
            L.append("| " + r["feature"] + " | " + r["us"] + " | " + " | ".join(r["them"]) + " |")
        L += ["", "Sources:"] + [f"- {v['name']}: {v['url']}" for v in smap.values()]
        if lp.get("comparePath"): L += ["", f"Full comparison page: {url(lp['comparePath'])}"]
    write_file(lp["path"] + "llms.txt", "\n".join(L) + "\n")

def write_file(path, doc):  # a page with an explicit file name, e.g. /raimaction/compare.html
    out = os.path.join(ROOT, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

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
            smap = c.get("sourceMap")
            for r in c["rows"]:
                if len(r["them"]) != n: errs.append(f"{p['slug']}: row '{r['feature']}' has {len(r['them'])} cells, expected {n}")
                if smap is not None:  # sourced comparison: every verified cell must name a source that exists
                    srcs = r.get("themSrc") or []
                    if len(srcs) != n: errs.append(f"{p['slug']}: row '{r['feature']}' themSrc has {len(srcs)} entries, expected {n}")
                    for v, sid in zip(r["them"], srcs):
                        if v != "—" and sid not in smap: errs.append(f"{p['slug']}: row '{r['feature']}' cell '{v}' has no valid source ({sid})")
                    if r.get("usSrc") not in smap: errs.append(f"{p['slug']}: row '{r['feature']}' our cell has no valid source")
        for key in ("advantages", "honest"):
            for a in (p.get("compare") or {}).get(key, []):
                if not (isinstance(a, dict) and a.get("t") and a.get("d")):
                    errs.append(f"{p['slug']}: compare.{key} entries need t and d")
        if p.get("poweredByRaimovia") and p["slug"] != "raimcalls":
            errs.append(f"{p['slug']}: poweredByRaimovia is only true for RaimCalls")
        for word, most in p.get("wordLimits", {}).items():  # e.g. RaimAction says TEAM UP, "co-op" at most once
            own = json.dumps({k: p.get(k) for k in ("tagline", "summary", "who", "features", "notes", "howto", "faq", "seoTitle", "seoDescription", "landing")}).lower()
            if own.count(word.lower()) > most: errs.append(f"{p['slug']}: '{word}' appears {own.count(word.lower())}x in our own copy (max {most})")
        if "aggregaterating" in json.dumps(p).lower() or "ratingvalue" in json.dumps(p).lower():
            errs.append(f"{p['slug']}: no ratings in structured data — we never publish ratings we did not collect")
        text = json.dumps(p).lower()
        for bad in ("dr. oviawe\"", " md ", "physician", "not a 501(c)(3)", "not tax-deductible"):
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
        if not p.get("hidden") and p.get("landing"): game_landing(p)
    print(f"built {len([p for p in SITE['products'] if not p.get('hidden')])} product pages + home, compare, roadmap, legal, sitemap, robots, llms.txt")
