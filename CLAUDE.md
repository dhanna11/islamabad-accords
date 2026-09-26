# The Islamabad Accords · website repo

A static site: a click-through slideshow of the author's deck, plus the PDF edition. No framework, no build server.

## Files
- `index.html`: the slideshow, one self-contained page. It loads only Google Fonts from outside.
- `islamabad-accords.pdf`: the PDF edition, linked from the slideshow's PDF button.
- `islamabad-accords.md`: the plain-text edition, which the "Ask Claude" / "Ask ChatGPT" buttons point the AI at. Generated in the chat; never edit its text here.
- `.nojekyll`: keeps GitHub Pages from running Jekyll, which would turn `islamabad-accords.md` into an HTML page and break its URL.
- `deck/`: the deck export the slideshow is built from (`deck.json` for slide order and sections, `slides/*.html` for one slide each). This is the source. Do not hand-edit `index.html`.
- `build-slideshow.py`: regenerates `index.html` (and `preview.html`) from `deck/`. It needs only Python 3.
- `README.md`: the human steps for GitHub Pages and a custom domain.
- `.github/workflows/check.yml` and `tests/`: the check that runs on every PR (see "Checks" below).

## Tasks
### First-time setup
1. `git init`, commit everything except `preview.html`, and create a public GitHub repo, e.g. `gh repo create islamabad-accords --public --source=. --push`.
2. Turn on Pages from the main branch root:
   `gh api -X POST repos/{owner}/islamabad-accords/pages -f "source[branch]=main" -f "source[path]=/"`
3. Wait for the first deploy (`gh api repos/{owner}/islamabad-accords/pages/builds/latest`) and open `https://{owner}.github.io/islamabad-accords/`.
4. Optional custom domain: ask the author which domain to use first (one option floated: `accords.virtuouscityvision.com`). Then write it to a `CNAME` file, commit, and tell him the DNS record to add (a CNAME from the subdomain to `{owner}.github.io`). Enforce HTTPS once the certificate is issued.

### Where the deck lives
The author edits the deck in the Claude chat app, as a Slides artifact: https://claude.ai/artifact/LFbTXx3XuS6AvxPaidPiNC
Its published files `project/deck.json` and `project/slides/<id>.html` map one-to-one onto `deck/deck.json` and `deck/slides/<id>.html` here. The artifact is the upstream source; `deck/` is a copy of it.
The PDF edition has its own artifact, https://claude.ai/artifact/EQe2iJS9XMf37GSy1zjjSE, whose published `islamabad-accords.pdf` and `islamabad-accords.md` are the upstream copies of the repo's PDF and plain-text edition.

### Syncing from the deck ("sync from the deck")
1. List the artifact's files (Artifact tool, `action: "list"`, `scope: "files"`, the URL above) and read `project/deck.json` plus every `project/slides/*.html` (`action: "read"`, `paths`, `out_dir` in the scratchpad).
2. Compare with `deck/`, and do step 5 (the PDF and text edition) too. If none of them differs, stop: the site is current.
3. Otherwise copy the files over `deck/` (remove slides that are no longer in the artifact), run `python3 build-slideshow.py`, and delete `preview.html`.
4. Summarize for the author: slides added, removed or reordered, and which slides' text changed. Flag any removed or renamed slide id, since shared links to it will stop working.
5. The PDF and the plain-text edition come from their own artifact: https://claude.ai/artifact/EQe2iJS9XMf37GSy1zjjSE. Read its published files `islamabad-accords.pdf` and `islamabad-accords.md` (Artifact tool, `action: "read"`, `paths`, `out_dir` in the scratchpad). If either differs from the repo's copy, replace it and say so in the PR summary.
6. Commit and push to the working branch, and open a PR into `main` (merging it publishes the site).

### Updating after the deck changes (manual)
1. Replace `deck/deck.json` and `deck/slides/` with the new export, and `islamabad-accords.pdf` with the new PDF.
2. Run `python3 build-slideshow.py`.
3. Open `index.html` locally and step through a few slides, then commit and push.

### Checks
Every PR and every push to `main` runs `.github/workflows/check.yml`. Merge only when it is green.
1. Build check: `python3 build-slideshow.py` must print no warnings, and the `index.html` it writes must match the committed one (so `index.html` is never edited by hand or left stale after a deck or script change).
2. `tests/smoke.mjs`: opens `index.html` in Chromium and checks every slide link, content spilling off a slide, the Ask/PDF/feedback links, taps and keys, and that the control bar stays on one line at widths from 1280px down to 320px.
Run it locally before pushing: `cd tests && npm ci && npx playwright install chromium && node smoke.mjs` (where Chromium is preinstalled, skip the install step). If a check fails, fix the cause; never loosen or skip a check to get green.
It runs Chromium only, so it cannot catch iPhone-only (WebKit) behavior; check those on a phone.

## Rules
- The words on the slides are the author's. Never rewrite slide text here. Content changes happen upstream in the deck, then get re-exported.
- Keep the site static and self-contained. Don't add trackers, analytics or third-party scripts without asking.
- Every slide has a stable link (`index.html#<slide-id>`). Don't rename slide ids casually, since people may have shared them.
- Who edits what. The chat app owns the deck (`deck/`) and the PDF. This repo owns `build-slideshow.py`: the page wrapper, controls and animations are edited only here, never taken from a chat's copy of the script (it would silently undo fixes made here).
- The menu labels (`SECTION_LABEL`, `SLIDE_LABEL` in `build-slideshow.py`) are the author's wording. Change them only when the author gives the new wording, e.g. after a section is renamed in the deck.
- The same goes for `ASK_PROMPT` (the prompt the Ask buttons send) and `FEEDBACK` (the "Tell me on X" note) in `build-slideshow.py`. Keep the Ask buttons ordinary outbound links: no scripts or embeds.
- If the build warns about an icon missing from `ICONS`, add that icon's 24px line paths to `ICONS` rather than leaving the plain-circle fallback.
