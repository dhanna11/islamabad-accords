#!/usr/bin/env python3
"""Standalone slideshow of the deck (25 Sep 2026, author: "rather than a long scroll… a button to click next/previous,
like a slideshow… maybe some sexy animations"). Reads the deck export in deck/ beside this script (deck.json
+ slides/*.html, copied from the Slides artifact) and writes ONE self-contained page. The deck is the source; nothing here rewrites a slide's words.
  · <x-icon> (drawn by the Slides app) becomes inline SVG; <x-shape kind="arrow-right"> becomes a clipped block.
  · Speaker notes (<aside>) are dropped from view.
Outputs, beside this script: index.html (with a PDF link, for GitHub Pages) and preview.html (no file link, git-ignored).
  · Warns on stderr about any <x-icon> name missing from ICONS (it would draw as a plain circle)."""
import json, re, sys, html as H
from urllib.parse import quote
from pathlib import Path

HERE = Path(__file__).resolve().parent
# the deck export: deck/deck.json + deck/slides/*.html beside this script (override with DECK_DIR=…)
import os
DECK = Path(os.environ.get("DECK_DIR", HERE / "deck"))
# 29 Sep 2026 (author): the pitch is the front page. pitch/ holds its export (same format as deck/); index.html is built
# from it and full.html from deck/. Each page links to the other; old links to full-deck slides on the front page forward.
PITCH = Path(os.environ.get("PITCH_DIR", HERE / "pitch"))
# the one-pager as one slide (8 Oct 2026, author: "the one page should really be in slide format", not a jarring separate page)
ONEPAGE = Path(os.environ.get("ONEPAGE_DIR", HERE / "onepage"))
ONE_PDF = "islamabad-accords-one-page.pdf"   # the one-pager's PDF, the left of the two PDF buttons

OUT = HERE
PDF_NAME = "islamabad-accords.pdf"
# "Ask Claude" / "Ask ChatGPT" open a new chat with this prompt filled in. The wording is the author's; change it only on their word.
ASK_PROMPT = ("Read the Islamabad Accords at https://dhanna11.github.io/islamabad-accords/islamabad-accords-text.html. "   # 8 Oct 2026: the HTML copy of the text edition (ChatGPT's reader refuses the .md's text/markdown); the wording is unchanged
              "Summarize it in a few lines, then answer my questions about it. Be fair to both its strengths and its weaknesses, "
              "and where it falls short, suggest how the plan could be improved.")
ASK_LINKS = [("Claude", "https://claude.ai/new?q="), ("ChatGPT", "https://chatgpt.com/?q=")]
FEEDBACK = ("Found a way to improve it? Tell me on X: @thekingdavidjr", "https://x.com/thekingdavidjr")

# 24px line icons, stroke = currentColor (the slide sets color and size on the element)
ICONS = {
  "Chart": '<path d="M3 3v18h18"/><path d="M7 15v3"/><path d="M11 10v8"/><path d="M15 12v6"/><path d="M19 6v12"/>',
  "Check": '<path d="M20 6 9 17l-5-5"/>',
  "CheckCircle": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  "Clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  "Globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/>',
  "Home": '<path d="m3 11 9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
  "Key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m17 6 3 3"/><path d="m15 8 2 2"/>',
  "Lightbulb": '<path d="M9 18h6"/><path d="M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z"/>',
  "Lightning": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  "Link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  "Lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  "Search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  "Trust": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9c4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
  "Users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2a5 5 0 0 1 5.5 5.3"/>',
  "Verified": '<path d="M12 2.5 14.6 4.4 17.8 4.3 18.8 7.3 21.3 9.2 20.3 12.2 21.3 15.2 18.8 17.1 17.8 20.1 14.6 20 12 21.9 9.4 20 6.2 20.1 5.2 17.1 2.7 15.2 3.7 12.2 2.7 9.2 5.2 7.3 6.2 4.3 9.4 4.4z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  "Warning": '<path d="M12 3 2 20h20z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
}
SECTION_LABEL = {"open": "Cover", "how": "The mechanism", "architectural": "2 · The architecture",  # the pitch's sections (29 Sep 2026)
                 "plan": "1 · The plan", "delivers": "2 · What it delivers",  # the pitch, regrouped by what the slides do (author, 6 Oct 2026)
                 "cover": "Cover", "core": "The core thesis", "why": "Why Trump", "transactional": "1 · The transactional phase",
                 "institutions": "2 · Five institutions", "trades": "3 · Five trades", "horizon": "4 · The horizon",
                 "limits": "5 · Limits", "close": "The close", "appendix": "Appendix",
                 "references": "References", "one-page": "1 page"}   # one-page: the switch's own label (8 Oct 2026)
SLIDE_LABEL = {"why-me": "About the author", "ai-disclosure": "AI disclosure"}
# Slide ids the deck has dropped, mapped to the slide that now holds the same content, so links people shared keep working.
# Add an entry whenever a sync removes or renames an id; never delete one.
SLIDE_ALIASES = {
  "limits-a": "limit-1", "limits-b": "limit-3", "limits-c": "limit-6",   # 26 Sep 2026: one slide per limit
  "objections-1": "objection-1", "objections-2": "objection-4",          # 26 Sep 2026: one slide per objection
}
BUILD_WARNINGS = []

UNKNOWN_ICONS = set()

def icon(m):
    name, style = m.group(1), m.group(2)
    if name not in ICONS: UNKNOWN_ICONS.add(name)
    paths = ICONS.get(name, '<circle cx="12" cy="12" r="8"/>')
    return (f'<svg class="xi" viewBox="0 0 24 24" aria-hidden="true" style="{style}; flex-shrink:0; fill:none; stroke:currentColor; '
            f'stroke-width:1.6; stroke-linecap:round; stroke-linejoin:round">{paths}</svg>')

def clean(s):
    s = re.sub(r'<x-icon name="([A-Za-z]+)" style="([^"]*)"></x-icon>', icon, s)
    s = re.sub(r'<x-shape kind="arrow-right" style="([^"]*)"></x-shape>',
               r'<div class="xs-arrow" style="\1"></div>', s)
    s = re.sub(r"<aside>.*?</aside>", "", s, flags=re.S)
    return s

# the two pages, in the order the switch shows them (author, 29 Sep 2026: "Two button works": a Pitch | Full deck switch
# with the page you are on lit, so the bar says where you are as well as where you can go)
PAGES = [("one-page.html", "1\u00a0page"), ("index.html", "Pitch"), ("full.html", "Full deck")]   # 8 Oct 2026, author ("A"): the one-pager joins the switch, shortest to longest; a no-break space keeps "1 page" whole on narrow bars

def switch_html(here):
    """Both pages as one control: the current one lit (aria-current), the other a link. On narrow bars "Full deck" shows
    as "Full" (the word after the first space hides), so the bar keeps its line."""
    def lab(label):
        first, _, rest = label.partition(" ")
        return H.escape(first) + (f'<span class="seg-more"> {H.escape(rest)}</span>' if rest else "")
    segs = "".join(f'<span class="seg cur" aria-current="page">{lab(label)}</span>' if href == here
                   else f'<a class="seg other" href="{href}">{lab(label)}</a>' for href, label in PAGES)
    return f'<div class="switch" role="group" aria-label="One page, pitch or full deck">{segs}</div>'

def build(with_pdf, deck_dir=DECK, other=None, forward=None):
    """other = (href, label) of the sibling page; forward = (page, ids): slide ids to send on to that page (old links)."""
    deck = json.loads((deck_dir / "deck.json").read_text())
    order = deck["order"]
    starts = {v["start"]: k for k, v in deck["sections"].items()}
    sec, slides, menu, toc = "cover", [], [], []
    for i, sid in enumerate(order):
        if sid in starts:
            sec = starts[sid]; menu.append((i, SECTION_LABEL.get(sec, sec)))
        label = SLIDE_LABEL.get(sid, SECTION_LABEL.get(sec, sec))
        body = clean((deck_dir / "slides" / f"{sid}.html").read_text().strip())
        toc.append((sid, slide_title(body)))
        slides.append(f'<div class="stage" data-id="{sid}" data-label="{H.escape(label)}" aria-roledescription="slide" aria-label="{i+1} of {len(order)}">{body}</div>')
    menu_html = "".join(f'<li><button type="button" data-go="{i}">{H.escape(l)}</button></li>' for i, l in menu)
    # the PDF, Ask and feedback links go only in the Pages build (index.html), not the preview
    links = note = other_link = ""
    if with_pdf:
        ask = "".join(f'<a class="pdf" href="{H.escape(url + quote(ASK_PROMPT, safe=""))}" target="_blank" rel="noopener">'
                      f'<span class="ask-long">Ask </span>{name}</a>' for name, url in ASK_LINKS)
        links = (f'<div class="ask" role="group" aria-label="Ask an AI about the plan"><span class="ask-lbl" aria-hidden="true">Ask</span>{ask}</div>'
                 # 8 Oct 2026, author: "the side by side PDF buttons… one page and then full plan… remove them from the menu"
                 f'<div class="pdfs" role="group" aria-label="PDF"><span class="pdfs-lbl" aria-hidden="true">PDF</span>'
                 f'<a class="seg" href="{ONE_PDF}" target="_blank" rel="noopener">1&nbsp;page</a>'
                 f'<a class="seg" href="{PDF_NAME}" target="_blank" rel="noopener">Full<span class="seg-more"> plan</span></a></div>')
        # the Pitch / Full deck toggle sits at the left end of the bar, before the section menu
        here = {PITCH: "index.html", DECK: "full.html", ONEPAGE: "one-page.html"}[deck_dir]
        other_link = switch_html(here) if other else ""
        text, href = FEEDBACK
        note = f'<a class="note" href="{href}" target="_blank" rel="noopener">{H.escape(text)}</a>'
        menu_html += "".join(f'<li class="menu-ask"><a href="{H.escape(url + quote(ASK_PROMPT, safe=""))}" target="_blank" rel="noopener">Ask {name}</a></li>'
                             for name, url in ASK_LINKS) + f'<li class="menu-note">{note}</li>'
        if other: menu_html = f'<li class="menu-other">{switch_html(here)}</li>' + menu_html
    aliases = SLIDE_ALIASES if deck_dir == DECK else {}
    for old, new in aliases.items():
        if old in order: BUILD_WARNINGS.append(f"alias {old!r} is a live slide id again; remove it from SLIDE_ALIASES")
        if new not in order: BUILD_WARNINGS.append(f"alias {old!r} points to {new!r}, which is not in deck.json; point it at the slide that now holds that content")
    page = TEMPLATE
    if len(order) == 1:   # a one-slide page (the one-pager): no arrows, counter or key hint
        page = page.replace('<nav class="bar"', '<nav class="bar single"', 1).replace('<div class="hint">← → to move</div>\n', '', 1)
    kind = {PITCH: "pitch", DECK: "deck", ONEPAGE: "onepage"}.get(deck_dir, "deck")
    desc = ("The Islamabad Accords, an unofficial peace proposal for ending the US-Iran war and building a new security architecture "
            f"for the Middle East: {PAGE_ABOUT[kind].format(n=len(order))}. The complete plan in plain text: {SITE_URL}{TEXT_HTML}")
    page = page.replace("{{DESCRIPTION}}", H.escape(desc)).replace("{{ABOUT}}", about_html(kind, len(order), toc) if with_pdf else "")
    return page.replace("{{SLIDES}}", "\n".join(slides)).replace("{{MENU}}", menu_html).replace("{{PDF}}", links).replace("{{OTHER}}", other_link) \
                   .replace("{{NOTE}}", note).replace("{{TOTAL}}", str(len(order))) \
                   .replace("{{ALIASES}}", json.dumps(aliases)) \
                   .replace("{{FORWARD}}", json.dumps({"page": forward[0], "ids": sorted(forward[1])} if forward else {"page": "", "ids": []})) \
                   .replace("<title>The Islamabad Accords</title>", {PITCH: "<title>The Islamabad Accords</title>", DECK: "<title>The Islamabad Accords · Full deck</title>",
                                                                     ONEPAGE: "<title>The Islamabad Accords · One page</title>"}.get(deck_dir, "<title>The Islamabad Accords</title>"))

# For AI tools that read the page through a web fetch (8 Oct 2026, author: "leave some instructions in the html… easier to grok
# when a LLM looks at it"): fetch tools drop scripts, styles and comments, so the help is plain text, factual, no instructions
# to the model. A meta description and a text/markdown alternate in the head, and one visually hidden paragraph (the
# screen-reader technique) at the top of the page naming what the page is and where the whole plan is in plain text.
SITE_URL = "https://dhanna11.github.io/islamabad-accords/"
MD_NAME = "islamabad-accords.md"
PAGE_ABOUT = {"pitch": "the pitch, a {n}-slide slideshow of the plan (the site's front page)",
              "deck": "the full deck, all {n} slides of the plan",
              "onepage": "the one-pager, the whole plan on one slide"}

# The text edition is islamabad-accords.md, but GitHub Pages serves .md as text/markdown, which some AI web readers refuse
# (8 Oct 2026, ChatGPT: "the web reader rejected it because the server serves it as text/markdown"). So every build also
# writes the same text as text/plain (.txt) and as a bare HTML page, the copy the Ask buttons and the notes point at.
TXT_NAME, TEXT_HTML = "islamabad-accords.txt", "islamabad-accords-text.html"

def text_copies():
    md = (HERE / MD_NAME).read_text()
    (OUT / TXT_NAME).write_text(md)
    (OUT / TEXT_HTML).write_text(f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Islamabad Accords · plain text</title>
<meta name="description" content="The complete text of the Islamabad Accords, an unofficial peace proposal: every card, slide and source, as plain text.">
<link rel="alternate" type="text/markdown" href="{MD_NAME}">
<style>body {{ margin:0; background:#0a1628; color:#f0ece2; }} pre {{ white-space:pre-wrap; word-wrap:break-word; max-width:80ch; margin:32px auto; padding:0 16px;
  font: 16px/1.55 'Source Sans 3', 'Segoe UI', Arial, sans-serif; }}</style>
<pre>{H.escape(md)}</pre>
</html>
""")

def slide_title(body):
    """A slide's title for the contents list: its heading (h1/h2) as text, else its first paragraph."""
    text = lambda frag: re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", frag))).strip()
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", body, re.S)
    if m: return text(m.group(1))
    for attrs, frag in re.findall(r"<p([^>]*)>(.*?)</p>", body, re.S):   # skip the icon paragraphs (aria-hidden emoji)
        if "aria-hidden" not in attrs and re.search(r"[A-Za-z]", text(frag)): return text(frag)
    return ""

def about_html(kind, n, toc=()):
    page = PAGE_ABOUT[kind].format(n=n)
    # the contents, so a reader gets the page's structure without inferring it from the layout (8 Oct 2026: a web reader
    # miscounted the pitch's slides); numbered, with each slide's own link
    contents = " ".join(f"{i}. {H.escape(t or sid)} (#{sid})." for i, (sid, t) in enumerate(toc, 1))
    return (f'<p class="sr-only" id="about-this-page">The Islamabad Accords, an unofficial peace proposal for ending the US-Iran war and '
            f'building a new security architecture for the Middle East. This page is {page}; every slide\'s text is in this page, in order. '
            f'The complete plan in plain text (all cards, slides and sources), the best single source for reading or summarizing it: '
            f'{SITE_URL}{TEXT_HTML} (the same text as {SITE_URL}{TXT_NAME} and {SITE_URL}{MD_NAME}). Other editions: the pitch ({SITE_URL}), the full deck ({SITE_URL}full.html), the one-pager '
            f'({SITE_URL}one-page.html), the PDF ({SITE_URL}{PDF_NAME}), the one-page PDF ({SITE_URL}{ONE_PDF}) and the web edition '
            f'with clickable sources ({SITE_URL}web.html). An overview for AI tools: {SITE_URL}llms.txt.'
            + (f' The {n} slide{"s" if n != 1 else ""} on this page, in order: {contents}' if contents else '') + '</p>')

TEMPLATE = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>The Islamabad Accords</title>
<meta name="description" content="{{DESCRIPTION}}">
<link rel="alternate" type="text/markdown" href="islamabad-accords.md" title="The Islamabad Accords, the complete plan in plain text">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;700&family=Source+Sans+3:wght@400;600;700&display=swap">
<style>
  /* single dark look, by choice: it is the deck's own identity */
  :root { color-scheme: dark; --ink:#05090f; --navy:#0a1628; --deep:#070e18; --gold:#c9a84c; --gold-l:#e0c872; --gold-d:#8a7234;
          --paper:#f0ece2; --line:rgba(201,168,76,.22); --bar:56px; }
  /* iOS Safari inflates text inside the wide 1920px slide, except while it animates, so text jumped size when a slide finished entering */
  html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
  html, body { height: 100%; }
  body { margin:0; background: var(--ink); color: var(--paper); font-family:'Source Sans 3', 'Segoe UI', Arial, sans-serif;
         display:flex; flex-direction:column; overflow:hidden; }
  .viewport { position:relative; flex:1; min-height:0; overflow:hidden; cursor:default; touch-action: pan-y; }
  .stage { position:absolute; left:50%; top:50%; width:1920px; height:1080px; transform-origin: 0 0; visibility:hidden;
           box-shadow: 0 30px 80px rgba(0,0,0,.55); }
  .stage.on { visibility:visible; }
  .stage section { position:relative; width:1920px; height:1080px; box-sizing:border-box; overflow:hidden; }
  .stage section * { box-sizing:border-box; }
  .stage h1, .stage h2, .stage h3, .stage p, .stage ul, .stage ol { margin:0; }
  .stage hr { margin:0; border:0; }
  .stage x-icon, .stage .xi { display:block; }
  .xs-arrow { display:block; flex-shrink:0; clip-path: polygon(0 30%, 60% 30%, 60% 0, 100% 50%, 60% 100%, 60% 70%, 0 70%); }

  /* motion: runs only on navigation, so the first frame is complete at rest */
  @keyframes inR { from { opacity:0; transform: translateX(28px); } to { opacity:1; transform:none; } }
  @keyframes inL { from { opacity:0; transform: translateX(-28px); } to { opacity:1; transform:none; } }
  @keyframes rise { from { opacity:0; transform: translateY(18px); } to { opacity:1; transform:none; } }
  @keyframes out { from { opacity:1; } to { opacity:0; } }
  .stage.enter-f section { animation: inR .55s cubic-bezier(.2,.7,.2,1) both; }
  .stage.enter-b section { animation: inL .55s cubic-bezier(.2,.7,.2,1) both; }
  .stage.enter-f section > *:not([style*="position:absolute"]), .stage.enter-b section > *:not([style*="position:absolute"]) {
      animation: rise .6s cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--i, 0) * 70ms + 80ms); }
  .stage.leave { visibility:visible; animation: out .28s ease both; }
  @media (prefers-reduced-motion: reduce) { .stage, .stage * { animation: none !important; } }

  /* control bar */
  .bar { position:relative; height: calc(var(--bar) + env(safe-area-inset-bottom, 0px)); padding: 0 16px env(safe-area-inset-bottom, 0px);
         display:flex; align-items:center; gap:14px; background: var(--deep); border-top:1px solid var(--line); }
  .progress { position:absolute; left:0; top:-1px; height:2px; background: var(--gold); width:0; transition: width .45s cubic-bezier(.2,.7,.2,1); }
  .where { display:flex; align-items:baseline; gap:12px; min-width:0; flex:1; }
  .sect { font: 700 11px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:2.5px; text-transform:uppercase; color: var(--gold);
          background:none; border:0; padding:8px 0; cursor:pointer; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:60vw; }
  .sect::after { content:" ▾"; color: var(--gold-d); }
  .bar.single .btn, .bar.single .count { display:none; }   /* one slide: nothing to step through */
  .count { font: 400 11px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:1.5px; color: var(--gold-d); font-variant-numeric: tabular-nums; white-space:nowrap; }
  .btn { width:40px; height:40px; border-radius:50%; border:1px solid var(--gold-d); background: transparent; color: var(--gold-l);
         display:grid; place-items:center; cursor:pointer; transition: background .2s, border-color .2s, transform .15s; }
  .btn:hover { background: rgba(201,168,76,.12); border-color: var(--gold); }
  .btn:active { transform: scale(.94); }
  .btn:disabled { opacity:.3; cursor:default; }
  .btn svg { width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
  .pdf { font: 700 11px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:2px; color: var(--gold-l); text-decoration:none;
         border:1px solid var(--gold-d); border-radius:20px; padding:9px 14px; }
  .pdf:hover { background: rgba(201,168,76,.12); }
  .pdfs { display:inline-flex; align-items:center; border:1px solid var(--gold-d); border-radius:20px; flex:none; position:relative; }
  .pdfs-lbl { font: 400 9px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:1.5px; color: var(--gold-d); padding:0 2px 0 14px; }
  .pdfs .seg { font: 700 11px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:2px; padding:9px 14px; white-space:nowrap;
               color: var(--gold-l); text-decoration:none; }
  .pdfs .seg + .seg { border-left:1px solid var(--gold-d); }
  .pdfs .seg:hover { background: rgba(201,168,76,.12); }
  .ask { display:flex; align-items:center; gap:8px; }
  .ask-lbl { display:none; font: 400 9px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:1.5px; text-transform:uppercase; color: var(--gold-d); }
  .note { font: 400 10px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:1.5px; color: var(--gold-d); text-decoration:none; white-space:nowrap; }
  .note:hover { color: var(--gold-l); text-decoration:underline; }
  .viewport > .note { position:absolute; left:16px; bottom:12px; opacity:.8; z-index:2; }
  .menu-ask { display:none; }
  .menu-other { display:none; padding:6px 4px 10px; }  /* the Pitch | Full deck switch: in the bar on wide screens, in the menu on phones */
  .switch { display:inline-flex; border:1px solid var(--gold-d); border-radius:20px; overflow:hidden; flex:none; }
  .switch .seg { font: 700 11px/1 'JetBrains Mono', ui-monospace, monospace; letter-spacing:2px; padding:9px 14px; white-space:nowrap;
                 color: var(--gold-l); text-decoration:none; }
  .switch .seg + .seg { border-left:1px solid var(--gold-d); }
  .switch .seg.cur { background: var(--gold); color: var(--deep); }
  .switch a.seg:hover { background: rgba(201,168,76,.12); }
  .menu-ask:not(.menu-ask + .menu-ask) { border-top:1px solid var(--line); margin-top:6px; padding-top:6px; }
  .menu-ask a { display:block; padding:10px 12px; border-radius:4px; color: var(--gold-l); text-decoration:none;
                font: 700 11px/1.2 'JetBrains Mono', ui-monospace, monospace; letter-spacing:2px; text-transform:uppercase; }
  .menu-ask a:hover { background: rgba(201,168,76,.12); }
  .menu-ask + .menu-note { border-top:0; margin-top:0; }
  .menu-note { display:none; border-top:1px solid var(--line); margin-top:6px; padding:10px 12px 4px; }
  .menu-note .note { font: 400 13px/1.2 'Source Sans 3', 'Segoe UI', Arial, sans-serif; letter-spacing:0; }
  .sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0; }
  :focus-visible { outline: 2px solid var(--gold-l); outline-offset: 3px; }
  .menu { position:absolute; left:16px; bottom: calc(var(--bar) + env(safe-area-inset-bottom, 0px) + 8px); background: var(--deep);
          border:1px solid var(--line); border-radius:6px; padding:8px; margin:0; list-style:none; min-width:260px; max-width: calc(100vw - 32px);
          box-shadow: 0 20px 50px rgba(0,0,0,.6); z-index:5; }
  .menu button { display:block; width:100%; text-align:left; background:none; border:0; color: var(--paper); padding:10px 12px; border-radius:4px;
                 font: 400 16px/1.2 'Instrument Serif', Georgia, serif; cursor:pointer; }
  .menu button:hover, .menu button.cur { background: rgba(201,168,76,.12); color: var(--gold-l); }
  .hint { position:absolute; right:16px; bottom:12px; font: 400 10px/1 'JetBrains Mono', monospace; letter-spacing:1.5px; color: var(--gold-d);
          opacity:.8; pointer-events:none; }
  @media (max-width: 560px) { .hint { display:none; } .count { display:none; } }
  /* narrow screens keep the bar on one line: short Ask labels under a small "Ask" first, then (under 480px) the Ask links
     move into the section menu; the feedback note moves into the menu under 640px */
  @media (max-width: 1150px) {   /* was 760px; 800px since the Pitch | Full deck switch (29 Sep 2026); 1000px since the three-way switch; 1150px since the two PDF buttons (8 Oct 2026) */
    .bar { gap:8px; }
    .ask { gap:4px; position:relative; }
    .ask-lbl { display:block; position:absolute; left:50%; top:-12px; transform:translateX(-50%); }
    .ask-long { display:none; }
    .ask .pdf, .bar > .pdf { padding:9px 9px; letter-spacing:1px; }
    .pdfs-lbl { position:absolute; left:50%; top:-12px; transform:translateX(-50%); padding:0; }   /* the label moves above, like Ask's */
    .pdfs .seg { padding:9px 9px; letter-spacing:1px; }
    .pdfs .seg-more { display:none; }
  }
  @media (max-width: 900px) { .bar > .switch .seg { padding:9px 6px; letter-spacing:0; } .bar > .switch .seg-more { display:none; } }  /* the switch is wide: "Full deck" shows as "Full" under 900px */
  @media (max-width: 640px) { .viewport > .note { display:none; } .menu-note { display:block; } }
  @media (max-width: 599px) { .bar .ask { display:none; } .menu-ask { display:block; } }   /* 479px before the two PDF buttons (8 Oct 2026) */
  @media (max-width: 759px) { .bar > .switch { display:none; } .menu-other { display:block; } }  /* into the menu under 760px (640px before the three-way switch, 720px before the two PDF buttons, 8 Oct 2026) */
  @media (max-width: 420px) { .pdfs .seg { padding:9px 6px; letter-spacing:0; } }   /* phones: the PDF pair tighter */
  @media (max-width: 360px) { .bar { gap:4px; } .btn { width:34px; height:34px; } .pdfs .seg { padding:9px 4px; } }   /* the smallest phones: every control a little tighter */
</style>

<main class="viewport" id="vp" aria-live="polite">
{{ABOUT}}
{{SLIDES}}
<div class="hint">← → to move</div>
{{NOTE}}
</main>
<nav class="bar" aria-label="Slideshow controls">
  <div class="progress" id="prog"></div>
  {{OTHER}}
  <div class="where">
    <button class="sect" id="sect" type="button" aria-haspopup="true" aria-expanded="false">Cover</button>
    <span class="count" id="count">1 / {{TOTAL}}</span>
  </div>
  {{PDF}}
  <button class="btn" id="prev" type="button" aria-label="Previous slide"><svg viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"/></svg></button>
  <button class="btn" id="next" type="button" aria-label="Next slide"><svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg></button>
  <ul class="menu" id="menu" hidden>{{MENU}}</ul>
</nav>

<script>
(() => {
  const vp = document.getElementById('vp');
  const stages = Array.from(vp.querySelectorAll('.stage'));
  const N = stages.length;
  const $ = id => document.getElementById(id);
  let cur = 0;
  // stagger index for each slide's flow children
  stages.forEach(s => { const sec = s.querySelector('section'); if (!sec) return;
    Array.from(sec.children).forEach((c, i) => c.style.setProperty('--i', i)); });

  function fit() {
    const w = vp.clientWidth, h = vp.clientHeight, pad = Math.min(32, w * 0.03);
    const k = Math.min((w - 2 * pad) / 1920, (h - 2 * pad) / 1080);
    stages.forEach(s => { s.style.transform = `scale(${k}) translate(-50%, -50%)`; });
  }
  const ALIASES = {{ALIASES}};  // retired slide ids -> their current slide, so old shared links still land right
  const FORWARD = {{FORWARD}};  // on the front page: full-deck slide ids (and their aliases) that live on full.html
  function idxFromHash() {
    let id = decodeURIComponent(location.hash.slice(1));
    if (FORWARD.ids.includes(id)) { location.replace(FORWARD.page + '#' + encodeURIComponent(id)); return 0; }
    if (Object.hasOwn(ALIASES, id)) id = ALIASES[id];
    const i = stages.findIndex(s => s.dataset.id === id);
    return i >= 0 ? i : 0;
  }
  function show(i, animate) {
    i = Math.max(0, Math.min(N - 1, i));
    if (i === cur && stages[i].classList.contains('on')) return;
    const dir = i > cur ? 'f' : 'b', old = stages[cur];
    stages.forEach(s => s.classList.remove('enter-f', 'enter-b', 'leave'));
    if (animate && old !== stages[i]) { old.classList.remove('on'); old.classList.add('leave');
      setTimeout(() => old.classList.remove('leave'), 300); } else old.classList.remove('on');
    const s = stages[i]; s.classList.add('on');
    if (animate) { void s.offsetWidth; s.classList.add('enter-' + dir); }
    cur = i;
    $('count').textContent = `${i + 1} / ${N}`;
    $('sect').textContent = s.dataset.label;
    $('prog').style.width = ((i + 1) / N * 100) + '%';
    $('prev').disabled = i === 0; $('next').disabled = i === N - 1;
    const secs = Array.from(document.querySelectorAll('#menu button[data-go]'));
    secs.forEach((b, k) => { const start = +b.dataset.go, end = k + 1 < secs.length ? +secs[k + 1].dataset.go : N;
      b.classList.toggle('cur', i >= start && i < end); });
    const id = s.dataset.id; if (location.hash.slice(1) !== id) history.replaceState(null, '', '#' + id);
  }
  const go = d => show(cur + d, true);
  $('next').onclick = () => go(1); $('prev').onclick = () => go(-1);
  vp.addEventListener('click', e => { if (e.target.closest('a')) return; const r = vp.getBoundingClientRect();
    go(e.clientX - r.left > r.width / 2 ? 1 : -1); });
  document.addEventListener('keydown', e => {
    if (e.target.closest('input, textarea')) return;
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key) && !e.target.closest('button, a')) { e.preventDefault(); go(1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    else if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); go(-1); }
    else if (e.key === 'Home') show(0, true); else if (e.key === 'End') show(N - 1, true);
    else if (e.key === 'Escape') closeMenu();
  });
  let tx = null, ty = null;
  vp.addEventListener('touchstart', e => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  vp.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    // only a real swipe swallows the tap-click, so a swipe never also counts as a half-screen tap
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) { e.preventDefault(); go(dx < 0 ? 1 : -1); } tx = null; }, { passive: false });
  const menu = $('menu');
  function closeMenu() { menu.hidden = true; $('sect').setAttribute('aria-expanded', 'false'); }
  $('sect').onclick = e => { e.stopPropagation(); menu.hidden = !menu.hidden; $('sect').setAttribute('aria-expanded', String(!menu.hidden)); };
  menu.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; show(+b.dataset.go, true); closeMenu(); });
  document.addEventListener('click', e => { if (!e.target.closest('#menu, #sect')) closeMenu(); });
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', () => show(idxFromHash(), true));
  fit(); cur = idxFromHash(); show(cur, false);
})();
</script>
"""

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    full_ids = json.loads((DECK / "deck.json").read_text())["order"]
    pitch_ids = json.loads((PITCH / "deck.json").read_text())["order"]
    forward = ("full.html", (set(full_ids) | set(SLIDE_ALIASES)) - set(pitch_ids))
    (OUT / "index.html").write_text(build(True, PITCH, ("full.html", "Full deck"), forward))   # the front page: the pitch
    (OUT / "full.html").write_text(build(True, DECK, ("index.html", "Pitch")))               # the full deck
    (OUT / "one-page.html").write_text(build(True, ONEPAGE, ("index.html", "Pitch")))        # the one-pager, one slide
    text_copies()                                                                             # the text edition as .txt and HTML
    (OUT / "preview.html").write_text(build(False, PITCH))
    (OUT / "preview-full.html").write_text(build(False, DECK))
    print("index.html (pitch), full.html (full deck) and one-page.html (one-pager) written,", (OUT / "index.html").stat().st_size // 1024, ",",
          (OUT / "full.html").stat().st_size // 1024, "and", (OUT / "one-page.html").stat().st_size // 1024, "KB")
    for w in dict.fromkeys(BUILD_WARNINGS):
        print(f"warning: {w}", file=sys.stderr)
    for name in sorted(UNKNOWN_ICONS):
        print(f"warning: icon {name!r} is not in ICONS, so it draws as a plain circle; add its paths to ICONS", file=sys.stderr)
