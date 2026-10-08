// Smoke test for the built slideshow. Opens ../index.html in Chromium at desktop and phone widths and checks what has
// broken or could break: page errors, the control bar, every slide link, the outbound links, content spilling off a
// slide, and the files the page links to. Run from this folder: npm ci && npx playwright install chromium && node smoke.mjs
import { chromium, devices } from 'playwright';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
// 29 Sep 2026: two pages. index.html is the pitch (the front page, from pitch/); full.html is the full deck (from deck/).
const PAGES = [{ file: 'index.html', dir: 'pitch', others: [['one-page.html', '1 page'], ['full.html', 'Full deck']], here: 'Pitch' },
               { file: 'full.html', dir: 'deck', others: [['one-page.html', '1 page'], ['index.html', 'Pitch']], here: 'Full deck' }];
let PAGE, deck;
const MD_URL = 'https://dhanna11.github.io/islamabad-accords/islamabad-accords.md';

const failures = [];
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'}  ${what}`); if (!ok) failures.push(what); };

// files the page links to, and the one that keeps Pages from turning the .md into HTML
for (const f of ['islamabad-accords.pdf', 'islamabad-accords.md', '.nojekyll', 'full.html', 'one-page.html', 'islamabad-accords-one-page.pdf'])
  check(existsSync(path.join(ROOT, f)) && (f === '.nojekyll' || statSync(path.join(ROOT, f)).size > 1000), `${f} is present`);

// the one-pager's web page links its own PDF and leads back to the slideshow
{
  const op = existsSync(path.join(ROOT, 'one-page.html')) ? readFileSync(path.join(ROOT, 'one-page.html'), 'utf8') : '';
  check(op.includes('href="islamabad-accords-one-page.pdf"') && op.includes('href="index.html"') && op.includes('href="full.html"') && /class="seg cur" aria-current="page">1(&nbsp;|\u00a0| )page</.test(op),
    'one-page.html links its PDF, carries the switch with "1 page" lit, and links the pitch and the full deck');
}

const browser = await chromium.launch();

async function open(contextOptions, hash = '') {
  const ctx = await browser.newContext(contextOptions);
  // never let a test click reach the real sites
  await ctx.route(/claude\.ai|chatgpt\.com|x\.com/, r => r.fulfill({ body: 'ok', contentType: 'text/plain' }));
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(PAGE + hash);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  return { ctx, page, errors };
}

for (const P of PAGES) {
PAGE = 'file://' + path.join(ROOT, P.file);
deck = JSON.parse(readFileSync(path.join(ROOT, P.dir, 'deck.json'), 'utf8'));
// a slide in the middle of this deck, for the navigation checks (3 Oct 2026: was a hard-coded id that left the pitch)
const MID = deck.order[Math.floor(deck.order.length / 2)];
console.log(`\n${P.file} (${P.dir}/, ${deck.order.length} slides)`);
// desktop: slides, links, spill
{
  const { ctx, page, errors } = await open({ viewport: { width: 1280, height: 800 } });

  const ids = await page.evaluate(() => [...document.querySelectorAll('.stage')].map(s => s.dataset.id));
  check(JSON.stringify(ids) === JSON.stringify(deck.order), `the page has all ${deck.order.length} slides, in deck.json order`);

  const wrong = [];
  for (const id of deck.order) {
    await page.evaluate(i => { location.hash = i; }, id);
    await page.waitForFunction(i => document.querySelector('.stage.on')?.dataset.id === i, id, { timeout: 2000 }).catch(() => wrong.push(id));
  }
  check(wrong.length === 0, `every slide link #<id> opens its slide${wrong.length ? ': ' + wrong.join(', ') : ''}`);

  // retired ids (SLIDE_ALIASES in build-slideshow.py) must still open the slide that took over their content (full deck)
  const aliases = JSON.parse(readFileSync(path.join(ROOT, P.file), 'utf8').match(/const ALIASES = (\{.*?\});/)[1]);
  if (P.dir === 'deck') {
  const badAlias = [];
  for (const [old, now] of Object.entries(aliases)) {
    await page.goto(PAGE + '#' + old);
    await page.waitForFunction(i => document.querySelector('.stage.on')?.dataset.id === i && location.hash === '#' + i, now, { timeout: 2000 })
      .catch(() => badAlias.push(`${old} -> ${now}`));
  }
  check(Object.keys(aliases).length > 0 && badAlias.length === 0,
    `old slide links redirect to their new slides (${Object.keys(aliases).length})${badAlias.length ? ': ' + badAlias.join(', ') : ''}`);
  } else {
    // links shared before the pitch became the front page point at full-deck slides on index.html: they must forward
    const fwd = JSON.parse(readFileSync(path.join(ROOT, P.file), 'utf8').match(/const FORWARD = (\{.*?\});/)[1]);
    const badFwd = [];
    for (const [id, want] of [['recon-gap', 'recon-gap'], ['limit-3', 'limit-3'], ['limits-a', 'limit-1']]) {
      await page.goto(PAGE + '#' + id);
      await page.waitForFunction(w => location.pathname.endsWith('/full.html') && document.querySelector('.stage.on')?.dataset.id === w, want, { timeout: 3000 })
        .catch(() => badFwd.push(`${id} -> full.html#${want}`));
    }
    check(fwd.page === 'full.html' && fwd.ids.length > 0 && badFwd.length === 0,
      `old front-page links to full-deck slides forward to full.html (${fwd.ids.length} ids)${badFwd.length ? ': ' + badFwd.join(', ') : ''}`);
    await page.goto(PAGE);
  }

  // content drawn outside the 1920x1080 slide is cut off; padding past the edge is harmless, so measure the elements
  const spill = await page.evaluate(() => [...document.querySelectorAll('.stage section')].flatMap(sec => {
    const box = sec.getBoundingClientRect(), k = box.width / 1920, out = [];
    for (const el of sec.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const over = Math.max(r.right - box.right, r.bottom - box.bottom, box.left - r.left, box.top - r.top) / k;
      if (over > 2) { out.push(`${sec.id} (${Math.round(over)}px)`); break; }
    }
    return out;
  }));
  check(spill.length === 0, `no slide content spills past the slide edge${spill.length ? ': ' + spill.join(', ') : ''}`);

  // the bar's own links (the section menu, also inside the bar, holds phone copies of the Ask links and the note)
  const other = await page.evaluate(() => ['.bar > .switch', '#menu .menu-other'].map(sel =>
    [...document.querySelectorAll(sel + ' a')].map(a => [a.getAttribute('href'), a.textContent.replace(/\s+/g, ' ').trim()])));
  check(other.every(links => JSON.stringify(links) === JSON.stringify(P.others)),
    `the switch in the bar and in the menu links to ${P.others.map(([h, t]) => `${h} ("${t}")`).join(' and ')}`);
  // the switch says where you are: this page's half is lit and marked current, in the bar and in the menu
  const here = await page.evaluate(() => [...document.querySelectorAll('.bar > .switch [aria-current="page"], #menu .menu-other [aria-current="page"]')].map(e => e.textContent.replace(/\s+/g, ' ').trim()));
  check(here.length === 2 && here.every(t => t === P.here), `the switch marks "${P.here}" as the page you are on`);
  const links = await page.evaluate(() => [...document.querySelectorAll('.bar > .ask a, .bar > .pdf:not(.other), .viewport > .note')].map(a => ({
    text: a.textContent.trim(), href: a.href, target: a.target, rel: a.rel })));
  const ask = links.filter(l => /^Ask /.test(l.text));
  check(ask.length === 2 && ask[0].href.startsWith('https://claude.ai/new?q=') && ask[1].href.startsWith('https://chatgpt.com/?q='),
    'the Ask buttons point to claude.ai/new?q= and chatgpt.com/?q=');
  check(ask.every(l => decodeURIComponent(new URL(l.href).searchParams.get('q') || '').includes(MD_URL)),
    'both Ask prompts point the AI at the text edition');
  check(links.some(l => l.text === 'PDF' && l.href.endsWith('/islamabad-accords.pdf')), 'the PDF button links to islamabad-accords.pdf');
  check(links.some(l => l.href === 'https://x.com/thekingdavidjr'), 'the feedback note links to x.com/thekingdavidjr');
  const menuLinks = await page.evaluate(() => [...document.querySelectorAll('#menu li:not(.menu-other) a')].map(a => ({ href: a.href, target: a.target, rel: a.rel })));
  check(menuLinks.length === 3 && menuLinks.slice(0, 2).map(l => l.href).join() === ask.map(l => l.href).join(),
    "the section menu's phone copies of the Ask links match the bar's");
  check([...links, ...menuLinks].every(l => l.target === '_blank' && l.rel.includes('noopener')), 'outbound links open a new tab with rel=noopener');

  await page.evaluate(id => { location.hash = id; }, MID);
  const [tab] = await Promise.all([ctx.waitForEvent('page'), page.locator('.ask a').first().click()]);
  await tab.waitForLoadState().catch(() => {});
  check(tab.url().startsWith('https://claude.ai/new?q=') && (await page.evaluate(() => location.hash)) === '#' + MID,
    'clicking Ask Claude opens a new tab and the slideshow stays on its slide');

  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(200);
  check((await page.evaluate(() => document.querySelector('.stage.on').dataset.id)) === deck.order[deck.order.indexOf(MID) + 1],
    'the right arrow key moves one slide forward');
  check(errors.length === 0, `no page errors on desktop${errors.length ? ': ' + errors.join('; ') : ''}`);
  await ctx.close();
}

// every width: the bar stays one line and the section menu button keeps room to be read and tapped
for (const width of [1280, 1024, 1023, 801, 800, 761, 760, 600, 480, 479, 390, 320]) {
  const phone = width <= 760;
  const { ctx, page, errors } = await open(phone ? { ...devices['iPhone 13'], viewport: { width, height: 800 } } : { viewport: { width, height: 800 } }, '#' + MID);
  const m = await page.evaluate(() => {
    const bar = document.querySelector('.bar'), vis = e => e.offsetParent !== null;
    const otherReachable = [...document.querySelectorAll('.bar > .switch, #menu .menu-other')].some(e => getComputedStyle(e).display !== 'none');
    const inBar = [...bar.querySelectorAll('a')].filter(vis).map(a => a.textContent.trim());
    const inMenu = [...document.querySelectorAll('#menu .menu-ask')].filter(li => getComputedStyle(li).display !== 'none').length;
    return { overflow: bar.scrollWidth - bar.clientWidth, sect: document.getElementById('sect').getBoundingClientRect().width,
             minH: Math.min(...[...bar.querySelectorAll('.ask a, .bar > .pdf, .btn')].filter(vis).map(e => e.getBoundingClientRect().height)),
             askReachable: inBar.filter(t => /Claude|ChatGPT/.test(t)).length === 2 || inMenu === 2, otherReachable };
  });
  check(m.overflow <= 0 && m.sect >= 100 && m.minH >= 28 && m.askReachable && m.otherReachable,
    `${width}px: bar fits on one line, section button ${Math.round(m.sect)}px wide, controls tappable, both Ask links and the switch (1 page, Pitch, Full deck) reachable`);

  if (width === 390) {
    const before = await page.evaluate(() => document.querySelector('.stage.on').dataset.id);
    const vp = await page.locator('#vp').boundingBox();
    await page.touchscreen.tap(vp.x + vp.width * 0.8, vp.y + vp.height / 2);
    await page.waitForTimeout(300);
    const after = await page.evaluate(() => document.querySelector('.stage.on').dataset.id);
    check(after === deck.order[deck.order.indexOf(before) + 1], '390px: tapping the right half of a slide moves one slide forward');
  }
  check(errors.length === 0, `${width}px: no page errors${errors.length ? ': ' + errors.join('; ') : ''}`);
  await ctx.close();
}

}  // end of the per-page loop

await browser.close();
console.log(failures.length ? `\n${failures.length} check(s) failed` : '\nall checks passed');
process.exit(failures.length ? 1 : 0);
