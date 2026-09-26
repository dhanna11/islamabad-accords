#!/usr/bin/env python3
"""Standalone slideshow of the deck (25 Sep 2026, author: "rather than a long scroll… a button to click next/previous,
like a slideshow… maybe some sexy animations"). Reads the deck export in deck/ beside this script (deck.json
+ slides/*.html, copied from the Slides artifact) and writes ONE self-contained page. The deck is the source; nothing here rewrites a slide's words.
  · <x-icon> (drawn by the Slides app) becomes inline SVG; <x-shape kind="arrow-right"> becomes a clipped block.
  · Speaker notes (<aside>) are dropped from view.
Outputs, beside this script: index.html (with a PDF link, for GitHub Pages) and preview.html (no file link, git-ignored).
  · Warns on stderr about any <x-icon> name missing from ICONS (it would draw as a plain circle)."""
import json, re, sys, html as H
from pathlib import Path

HERE = Path(__file__).resolve().parent
# the deck export: deck/deck.json + deck/slides/*.html beside this script (override with DECK_DIR=…)
import os
DECK = Path(os.environ.get("DECK_DIR", HERE / "deck"))
OUT = HERE
PDF_NAME = "islamabad-accords.pdf"

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
SECTION_LABEL = {"cover": "Cover", "core": "The core thesis", "why": "Why Trump", "transactional": "1 · The transactional phase",
                 "institutions": "2 · Five institutions", "trades": "3 · Five trades", "horizon": "4 · The horizon",
                 "limits": "5 · Limits", "references": "References"}
SLIDE_LABEL = {"why-me": "About the author", "ai-disclosure": "AI disclosure"}

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

def build(with_pdf):
    deck = json.loads((DECK / "deck.json").read_text())
    order = deck["order"]
    starts = {v["start"]: k for k, v in deck["sections"].items()}
    sec, slides, menu = "cover", [], []
    for i, sid in enumerate(order):
        if sid in starts:
            sec = starts[sid]; menu.append((i, SECTION_LABEL.get(sec, sec)))
        label = SLIDE_LABEL.get(sid, SECTION_LABEL.get(sec, sec))
        body = clean((DECK / "slides" / f"{sid}.html").read_text().strip())
        slides.append(f'<div class="stage" data-id="{sid}" data-label="{H.escape(label)}" aria-roledescription="slide" aria-label="{i+1} of {len(order)}">{body}</div>')
    menu_html = "".join(f'<li><button type="button" data-go="{i}">{H.escape(l)}</button></li>' for i, l in menu)
    pdf_btn = f'<a class="pdf" href="{PDF_NAME}" target="_blank" rel="noopener">PDF</a>' if with_pdf else ""
    return TEMPLATE.replace("{{SLIDES}}", "\n".join(slides)).replace("{{MENU}}", menu_html).replace("{{PDF}}", pdf_btn) \
                   .replace("{{TOTAL}}", str(len(order)))

TEMPLATE = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>The Islamabad Accords</title>
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
</style>

<main class="viewport" id="vp" aria-live="polite">
{{SLIDES}}
<div class="hint">← → to move</div>
</main>
<nav class="bar" aria-label="Slideshow controls">
  <div class="progress" id="prog"></div>
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
  function idxFromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
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
    document.querySelectorAll('#menu button').forEach(b => {
      const start = +b.dataset.go, next = b.parentElement.nextElementSibling;
      const end = next ? +next.firstElementChild.dataset.go : N; b.classList.toggle('cur', i >= start && i < end); });
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
    (OUT / "index.html").write_text(build(True))
    (OUT / "preview.html").write_text(build(False))
    print("index.html and preview.html written", (OUT / "index.html").stat().st_size // 1024, "KB")
    for name in sorted(UNKNOWN_ICONS):
        print(f"warning: icon {name!r} is not in ICONS, so it draws as a plain circle; add its paths to ICONS", file=sys.stderr)
