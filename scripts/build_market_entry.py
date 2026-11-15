#!/usr/bin/env python3
"""Builds market-entry.html (Swedish Market Entry, in English) from the
calculator's own values in index.html.

Prices per video, median views, the volume-discount ladder and the Spark Ads
surcharges are read straight out of index.html, exactly like
build_pricing.py, so this page, priser.html and the calculator can never show
different numbers. The design (fonts + CSS) is read from affiliate.html so the
page keeps the site's white-and-pink theme. Runs nightly in stats.yml.

The package (Love, 13 Nov 2026): 2 creators of the Biggest class (a Top
creator steps in when one is booked, and the price drops by the difference),
3 Large creators and 5 Mid-size creators, one video each, plus the 3 smaller
creators that always come free.
"""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
h = (root / "index.html").read_text(encoding="utf-8")
aff = (root / "affiliate.html").read_text(encoding="utf-8")

TIERS = {k: {"label": l, "range": r, "max": int(m), "price": int(p), "views": int(v)}
         for k, l, r, m, p, v in re.findall(
             r"\{key:'(\w+)',\s*label:'([^']+)',\s*range:'([^']+)',\s*max:(\d+),\s*price:(\d+),\s*views:(\d+)\}", h)}
SPARK = [{"label": l, "up": int(u)} for l, u in re.findall(r"\{label:'([^']+)',\s*up:\.(\d+)\}", h)]
d = re.search(r'return videos>=26\?(\d+) : videos>=20\?(\d+) : videos>=15\?(\d+) : videos>=10\?(\d+) : videos>=6\?(\d+) : videos>=3\?(\d+)', h)
LADDER = [(26, int(d.group(1))), (20, int(d.group(2))), (15, int(d.group(3))),
          (10, int(d.group(4))), (6, int(d.group(5))), (3, int(d.group(6)))]
fr = re.search(r"KM_FREE = \{count:(\d+), views:(\d+)\}", h)
FREE_N, FREE_VIEWS = int(fr.group(1)), int(fr.group(2))
for key in ("storst", "topp", "stor", "mellan"):
    assert key in TIERS, f"tier {key} missing in index.html"
assert len(SPARK) == 4, "Spark ladder not found in index.html"

EN_LABEL = {"storst": "Biggest", "topp": "Top", "stor": "Large", "mellan": "Mid-size"}
EN_SPARK = {"30 dagar": "30 days", "90 dagar": "90 days", "6 månader": "6 months", "12 månader": "12 months"}
EN_RANGE = lambda r: r.replace("följare", "followers")


def discount(videos):
    for threshold, pct in LADDER:
        if videos >= threshold:
            return pct
    return 0


def package(head_key):
    rows = [(head_key, 2), ("stor", 3), ("mellan", 5)]
    for k, n in rows:
        assert n <= TIERS[k]["max"], f"network has only {TIERS[k]['max']} in {k}"
    paid = sum(n for _, n in rows)
    lst = sum(TIERS[k]["price"] * n for k, n in rows)
    disc = discount(paid)
    saved = lst * disc / 100
    views = sum(TIERS[k]["views"] * n for k, n in rows) + FREE_VIEWS
    return {"rows": rows, "paid": paid, "list": lst, "disc": disc, "saved": saved,
            "final": lst - saved, "views": views, "videos": paid + FREE_N}


P = package("storst")
ALT = package("topp")

num = lambda n: f"{int(round(n)):,}".replace(",", "&nbsp;")
sek = lambda n: "SEK&nbsp;" + num(n)
plain_sek = lambda n: "SEK " + f"{int(round(n)):,}".replace(",", " ")
kviews = lambda n: (f"{n / 1e6:.1f} M") if n >= 1e6 else f"{round(n / 1000):,}K"

# Design: the font face + the two style blocks of affiliate.html, unchanged.
css = re.search(r'(<link rel="preload" href="/assets/fonts/schibsted-grotesk\.woff2"[\s\S]*?</style>\s*<style>[\s\S]*?</style>)', aff).group(1)
logo = re.search(r'(<svg viewBox="0 0 400 435" aria-hidden="true">[\s\S]*?</svg>)', aff).group(1)
BOOK = "https://calendar.app.google/8vFghCDtFN2itfJU8"

price_rows = "\n".join(
    f'''        <tr><th scope="row">{n} × {EN_LABEL[k]}<small>{EN_RANGE(TIERS[k]["range"])}</small><small class="mv-in">{num(TIERS[k]["views"])} median views</small></th>'''
    f'''<td class="num">{sek(TIERS[k]["price"])}</td><td class="num mv">{num(TIERS[k]["views"])}</td>'''
    f'''<td class="num"><b>{sek(TIERS[k]["price"] * n)}</b></td></tr>''' for k, n in P["rows"])

spark_rows = "\n".join(
    f'''        <tr><th scope="row">{EN_SPARK.get(s["label"], s["label"])}</th><td class="num">+{s["up"]}&nbsp;%</td>'''
    f'''<td class="num"><b>{sek(P["list"] * s["up"] / 100)}</b></td></tr>''' for s in SPARK)

faq = [
    ("What does Swedish Market Entry cost?",
     f"{plain_sek(P['final'])} excluding VAT for {P['paid']} creators with one video each: two of the biggest creators in our network, "
     f"three large and five mid-size. That is the list price of {plain_sek(P['list'])} minus our {P['disc']} % volume discount. "
     f"{FREE_N} smaller creators come on top at no cost, so you get {P['videos']} videos."),
    ("Why these three kinds of creators?",
     "Each layer does one job. The two biggest creators give a brand nobody in Sweden knows yet its credibility. "
     "The three large creators carry the launch to the widest audience. The five mid-size creators make sure the same buyers "
     "see you again, from someone else, in the same weeks."),
    ("Are the videos in Swedish?",
     "Yes. Swedish creators make the videos on their own TikTok accounts, in Swedish, for their Swedish audience. "
     "That is the point: it is how a Swedish buyer meets your brand from someone they already follow."),
    ("Can we choose the creators?",
     "Yes. We propose the ten creators with their numbers and why each fits your product, and you approve before anything is locked. "
     "You also approve every script and every finished video before it is published."),
    ("What if one of the biggest creators is booked?",
     f"Then a Top creator ({EN_RANGE(TIERS['topp']['range'])}) takes the place and you pay the difference less. "
     f"With two Top creators the package is {plain_sek(ALT['final'])}."),
    ("Is the reach guaranteed?",
     f"We set a floor for the campaign, built on each creator's median over her last 20 videos — about {kviews(P['views'])} views for this package. "
     "If the campaign does not reach the floor, we add an extra video from one of our smaller creators at no cost. We can promise it because "
     "we measure every account every night."),
    ("Are the videos marked as advertising?",
     "Yes. Swedish law requires advertising to be clearly marked from the start. Every creator gets a ready caption with the ad marking, "
     "TikTok's branded-content toggle is switched on, and we check both before a video counts as delivered."),
    ("Can we run the videos as ads?",
     "Yes, with Spark Ads as an add-on. You buy the rights after publication, when you have seen what each video did organically, and run them "
     "from your own TikTok ad account. The media budget is yours; if you want us to set up and optimise the campaigns we charge 15 % of the media spend."),
]
faq_html = "\n".join(f'''    <details{" open" if i == 0 else ""}><summary>{q}</summary><p>{a}</p></details>''' for i, (q, a) in enumerate(faq))
schema = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/luminate-icon-96.png" sizes="96x96">
<link rel="icon" type="image/png" href="/assets/luminate-icon-192.png" sizes="192x192">
<link rel="icon" type="image/svg+xml" href="/assets/luminate-icon.svg">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<title>Swedish Market Entry — launch in Sweden with 10 Swedish TikTok creators — Luminate Media</title>
<meta name="description" content="A fixed-price TikTok creator campaign for brands entering Sweden: 2 of Sweden's biggest creators for credibility, 3 large for reach and 5 mid-size for repeat exposure. {plain_sek(P['final'])} excl. VAT, {P['videos']} videos.">
<link rel="canonical" href="https://www.luminatemedia.se/market-entry.html">
<meta name="theme-color" content="#FFFFFF">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_GB">
<meta property="og:site_name" content="Luminate Media">
<meta property="og:url" content="https://www.luminatemedia.se/market-entry.html">
<meta property="og:title" content="Swedish Market Entry: launch in Sweden with 10 Swedish TikTok creators">
<meta property="og:description" content="Credibility, reach and repeat exposure in one fixed-price package. {plain_sek(P['final'])} excl. VAT.">
<meta property="og:image" content="https://www.luminatemedia.se/assets/og-share.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=1)}
</script>
{css}
<style>
/* Swedish Market Entry: the package table */
.pk-wrap{{background:#fff;border:1px solid rgba(0,0,0,.07);border-radius:var(--r);box-shadow:var(--shadow);overflow-x:auto;overscroll-behavior-x:contain;margin-top:28px}}
.pk{{min-width:560px;table-layout:auto}}
.pk th,.pk td{{padding:14px 18px;border-bottom:1px solid var(--line2);text-align:left;vertical-align:top}}
.pk thead th{{font-size:13px;font-weight:600;color:var(--faint);letter-spacing:.02em}}
.pk tbody th{{font-weight:700}}
.pk th small{{display:block;font-weight:400;color:var(--faint);font-size:13px;margin-top:2px}}
.pk .num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.pk tfoot th,.pk tfoot td{{border-bottom:0}}
.pk tr.tot th,.pk tr.tot td{{font-size:20px;font-weight:800;color:var(--plum);border-top:2px solid var(--pink-2)}}
.pk tr.dim th,.pk tr.dim td{{color:var(--muted);font-weight:500}}
.why{{color:var(--muted);margin-top:10px}}
.why b{{color:var(--txt)}}
.tier .t-role{{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--rose);margin-bottom:6px}}
.pk .mv-in{{display:none}}
@media (max-width:640px){{.pk{{min-width:0}}.pk th,.pk td{{padding:12px 12px}}.pk .mv{{display:none}}.pk .mv-in{{display:block}}.pk tr.tot th,.pk tr.tot td{{font-size:17px}}}}
.sec .after{{margin-top:18px;color:var(--muted);max-width:760px}}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<nav aria-label="Main menu">
  <a class="nav-brand" href="/" aria-label="Luminate Media — home">
    {logo}
    <b>Luminate</b>
  </a>
  <div class="nav-links">
    <a href="#package">Package</a>
    <a href="#price">Price</a>
    <a href="#results">Results</a>
    <a href="#faq">FAQ</a>
    <a class="nav-cta" href="{BOOK}" target="_blank" rel="noopener">Book 15 min</a>
  </div>
</nav>

<header class="hero">
  <div class="hero-in">
    <span class="eyebrow"><i></i>Swedish Market Entry · fixed price</span>
    <h1>Launch in Sweden with <span class="g">10 Swedish TikTok creators.</span></h1>
    <p class="hero-sub">One campaign built for a brand Sweden has not met yet: two of the country's biggest creators for credibility, three large ones for reach and five mid-size creators so the same buyers keep seeing you. You send the product. We do the rest.</p>
    <div class="ctas">
      <a class="book" href="{BOOK}" target="_blank" rel="noopener">Book 15 min</a>
      <a class="book ghost" href="#price">See the price ↓</a>
    </div>
    <ul class="facts">
      <li><span><b>{sek(P["final"])}</b> excl. VAT</span></li>
      <li><span><b>{P["videos"]}</b> videos</span></li>
      <li><span><b>≈&nbsp;{kviews(P["views"])}</b> estimated views</span></li>
    </ul>
  </div>
</header>

<main id="main">

<section class="sec alt" id="package" aria-labelledby="h-pack">
  <span class="label reveal">The package</span>
  <h2 id="h-pack" class="reveal">Three layers. <span class="g">Each one has a job.</span></h2>
  <p class="lead reveal">A new brand has three problems in a new market: nobody trusts it yet, nobody has seen it yet, and the people who saw it once have forgotten it by the time they shop. The package answers them in that order.</p>
  <div class="tiers">
    <div class="tier reveal">
      <span class="t-role">Credibility</span>
      <span class="t-name">2 × Biggest</span>
      <span class="t-vol">{EN_RANGE(TIERS["storst"]["range"])}</span>
      <p class="why">Nobody in Sweden has heard of you yet. When one of the country's <b>biggest creators</b> shows your product to her own audience, Swedish buyers see that someone they already trust has chosen you. That first signal is what the rest of the campaign builds on.</p>
    </div>
    <div class="tier reveal">
      <span class="t-role">Reach</span>
      <span class="t-name">3 × Large</span>
      <span class="t-vol">{EN_RANGE(TIERS["stor"]["range"])}</span>
      <p class="why">Three <b>large creators</b>, each with a median of {num(TIERS["stor"]["views"])} views per video, carry the launch to the widest possible audience while it is new — so the brand is seen by as many Swedish buyers as possible in the same weeks.</p>
    </div>
    <div class="tier reveal">
      <span class="t-role">Repeat exposure</span>
      <span class="t-name">5 × Mid-size</span>
      <span class="t-vol">{EN_RANGE(TIERS["mellan"]["range"])}</span>
      <p class="why">People rarely buy a brand the first time they see it. Five <b>mid-size creators</b>, each with her own loyal audience, make sure the same buyers meet you again from someone else — that is what turns "never heard of it" into "I keep seeing it everywhere".</p>
    </div>
  </div>
  <p class="after reveal">Plus <b>{FREE_N} smaller creators at no cost</b> — they always come with a campaign. Every creator makes one video on her own TikTok account, in Swedish.</p>
</section>

<section class="sec" id="price" aria-labelledby="h-price">
  <span class="label reveal">Price</span>
  <h2 id="h-price" class="reveal">One fixed price. <span class="g">Our own list prices.</span></h2>
  <p class="lead reveal">The same prices per video as on our <a href="/priser.html">price list</a>, priced on what each account actually delivers, not on follower count. Median views are measured on each creator's last 20 videos and read from TikTok every night. All prices excl. VAT.</p>
  <div class="pk-wrap reveal">
    <table class="pk">
      <thead><tr><th scope="col">Creators</th><th scope="col" class="num">Per video</th><th scope="col" class="num mv">Median views</th><th scope="col" class="num">Subtotal</th></tr></thead>
      <tbody>
{price_rows}
        <tr><th scope="row">{FREE_N} × Smaller creators<small>always included</small><small class="mv-in">{num(FREE_VIEWS)} views in total</small></th><td class="num">free</td><td class="num mv">{num(FREE_VIEWS)}&nbsp;in&nbsp;total</td><td class="num"><b>SEK&nbsp;0</b></td></tr>
      </tbody>
      <tfoot>
        <tr class="dim"><th scope="row" colspan="2">List price, {P["paid"]} videos</th><td class="mv"></td><td class="num">{sek(P["list"])}</td></tr>
        <tr class="dim"><th scope="row" colspan="2">Volume discount −{P["disc"]}&nbsp;%</th><td class="mv"></td><td class="num">−{sek(P["saved"])}</td></tr>
        <tr class="tot"><th scope="row" colspan="2">Swedish Market Entry, {P["videos"]} videos</th><td class="mv"></td><td class="num">{sek(P["final"])}</td></tr>
      </tfoot>
    </table>
  </div>
  <p class="after reveal">≈&nbsp;{kviews(P["views"])} estimated views, built on each class's actual median views, not on promises. If one of the two biggest creators is booked in your launch window, a Top creator ({EN_RANGE(TIERS["topp"]["range"])}) takes the place and the price drops by the difference — {sek(ALT["final"])} with two Top creators.</p>
  <p class="after reveal"><b>Included in every video:</b> concept, script, filming, editing, publishing, one revision round, deadline handling and reporting. You approve the script and the finished video before publication, and the video stays up for at least twelve months. Every video is measured every night, with a report on day 7 and day 30.</p>
</section>

<section class="sec alt" id="spark" aria-labelledby="h-spark">
  <span class="label reveal">Add-on</span>
  <h2 id="h-spark" class="reveal">Spark Ads: <span class="g">buy the winners.</span></h2>
  <p class="lead reveal">Want to advertise with the videos? Buy the rights after publication, when you have seen what each one did organically, and run them from your own TikTok ad account with the creator's name and engagement intact. The surcharge is on the creators' list price; the example is all {P["paid"]} paid videos in the package.</p>
  <div class="pk-wrap reveal">
    <table class="pk">
      <thead><tr><th scope="col">Rights period</th><th scope="col" class="num">Surcharge</th><th scope="col" class="num">Whole package</th></tr></thead>
      <tbody>
{spark_rows}
      </tbody>
    </table>
  </div>
  <p class="after reveal">You can also buy rights for just the best videos. The media budget is paid by you, in your own ad account, and stays yours. If you want us to set up and optimise the campaigns, we charge 15&nbsp;% of the media spend.</p>
</section>

<section class="sec" id="results" aria-labelledby="h-res">
  <span class="label reveal">Results</span>
  <h2 id="h-res" class="reveal">Counted on <span class="g">real numbers.</span></h2>
  <p class="lead reveal">14 TikTok videos for a Swedish clothing retailer: 430&nbsp;720 views organically — and 2.7 million once the client boosted them with Spark Ads.</p>
  <div class="res">
    <div class="r reveal"><b>≈&nbsp;90&nbsp;%</b><span>lower cost per 1&nbsp;000 views than the average</span><small>€0.38 against the average €3.78–4.28, when the videos ran as Spark Ads.</small></div>
    <div class="r reveal"><b>2.7&nbsp;million</b><span>views on 14 videos with the client's Spark Ads</span><small>2&nbsp;678&nbsp;700 views measured 7 Nov 2026, against 430&nbsp;720 organically before Spark Ads.</small></div>
    <div class="r reveal"><b>SEK&nbsp;0.75</b><span>per click</span><small>€0.067 against agency benchmarks of €0.18–0.82.</small></div>
  </div>
  <p class="note">Sources: autumn campaign 2026, Sweden, 14 creator videos in two periods. Views: TikTok's public counters, read by Luminate 7 Nov 2026; the figure with Spark Ads includes the client's ad views. Organic = views before Spark Ads started. Cost per 1&nbsp;000 views and cost per click: the campaign's ad account 5 Oct 2026, reach campaign; the €3.78–4.28 average is Triple Whale 2025 (apparel) and Lebesgue 2026; click benchmarks from Svenska Följare, Fullmetrix and Nonsensical for Sweden, Europe and the UK. The benchmarks partly cover other markets and campaign goals.</p>
</section>

<section class="sec alt" id="how" aria-labelledby="h-how">
  <span class="label reveal">How it works</span>
  <h2 id="h-how" class="reveal">Four steps. <span class="g">We run it.</span></h2>
  <ol class="steps">
    <li class="step reveal"><span class="step-n">1</span><h3>Book 15 minutes</h3><p>Tell us what you sell, who buys it and when you launch in Sweden.</p></li>
    <li class="step reveal"><span class="step-n">2</span><h3>Approve the creators</h3><p>You get a proposal of ten creators with their numbers and why each fits, within 48 hours. Nothing is locked until you approve it.</p></li>
    <li class="step reveal"><span class="step-n">3</span><h3>Send the product</h3><p>We brief every creator, write the scripts with them and send them to you for approval. You approve each finished video before it goes live.</p></li>
    <li class="step reveal"><span class="step-n">4</span><h3>See the results</h3><p>Views, engagement and every creator against her own normal level, measured every night, with a report on day 7 and day 30.</p></li>
  </ol>
</section>

<section class="sec" id="faq" aria-labelledby="h-faq">
  <span class="label reveal">FAQ</span>
  <h2 id="h-faq" class="reveal">What brands usually ask</h2>
  <div class="faq reveal">
{faq_html}
  </div>
</section>

<section class="contact" aria-labelledby="h-cta">
  <span class="label">Get started</span>
  <h2 id="h-cta">Launching in Sweden? <span>Let's plan the first weeks.</span></h2>
  <p>Book 15 minutes and we'll propose the ten creators for your product. Or email <a href="mailto:hello@luminatemedia.se">hello@luminatemedia.se</a>.</p>
  <div class="ctas">
    <a class="book" href="{BOOK}" target="_blank" rel="noopener">Book 15 min →</a>
    <a class="book ghost" href="/priser.html">Swedish price list</a>
  </div>
</section>

</main>

<footer>
  {logo}
  <div class="fl">
    <a href="/">Home (Swedish)</a>
    <a href="/priser.html">Price per video</a>
    <a href="/affiliate">Affiliate</a>
    <a href="/integritet.html">Privacy and cookies</a>
  </div>
  <div class="fl">
    <span>© 2026 Luminate Media · Org.nr 969804-5599</span>
    <span>Raketgatan 12 · Lund — Sweden</span>
  </div>
</footer>

<script>
(() => {{
const rv = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {{
  const io = new IntersectionObserver(es => es.forEach(x => {{ if (x.isIntersecting) {{ x.target.classList.add("in"); io.unobserve(x.target); }} }}), {{ rootMargin: "0px 0px -8% 0px" }});
  rv.forEach(n => io.observe(n));
}} else rv.forEach(n => n.classList.add("in"));
}})();
</script>
</body>
</html>
'''

(root / "market-entry.html").write_text(html, encoding="utf-8")
print(f"market-entry.html byggd — {P['paid']} kreatörer + {FREE_N} gratis, {plain_sek(P['final'])} "
      f"(lista {plain_sek(P['list'])}, −{P['disc']} %), ≈ {kviews(P['views'])} visningar; med 2 topp {plain_sek(ALT['final'])}")
