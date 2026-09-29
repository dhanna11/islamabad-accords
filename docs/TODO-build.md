# TODO · Build scripts into the repo, then one content source

Written 28 Sep 2026, 23:41, at the author's request. Planning only: nothing below has been started.

## Goal

1. **Build scripts into the repo.** Today the build lives only in this workspace and the handoff zip; the repo (dhanna11/islamabad-accords) holds only the published editions. Anyone, including a future code session, should be able to clone and rebuild every edition.
2. **One content source.** Every sentence lives once, in a structured content file that all six editions read. Most of `check-sync.py` then becomes unnecessary, because editions that share a source can't drift apart.

Do phase 0 first; A and B both depend on it. A comes before B, so the refactor happens in the repo with history.

## Inventory · where things live today

**Builders** (about 2,500 lines of Python):
| Script | Lines | Makes |
|---|---|---|
| `build-deck.py` + `deck-text.py` | 768 + 303 | 58 slides (`fit-deck.py` 106 fits the type) |
| `build-card-0.py`, `build-card-6.py` | 132, 221 | cover card, sources card (HTML from Python) |
| `build-why.py`, `build-whyme.py`, `build-title.py`, `build-disclosure.py` | 88, 30, 83, 56 | Why Trump, why-me, title, AI-disclosure pages |
| `render-v3.py` | 20 | card PNGs |
| `build-web.py` | 158 | web edition |
| `print/build-print.py` | 180 | 13-page print PDF |
| `build-onepage.py` | 123 | one-pager (content height must be 1165) |
| `build-text.py` | 104 | plain-text edition, `islamabad-accords.md` |
| `check-sync.py`, `check-lists.py`, `check-positioned.py` | 36, 19, 31 | drift, list ≤5, positioned ≤24 |
| `bulletize-cards.py` | 76 | one-time conversion from 20 Sep, already run → archive |

**Text lives in at least six places:**
- Card HTML, cards 1–5: hand-written, the ratified source. The deck parses these lists (`card_lists()` → C1–C5).
- `deck-text.py`: deck-only slides (SLIDES dict) and the CHROME pairs.
- `build-deck.py`: inline text (MECH, ARC, HZ, GATES, INST members and lineage, TABLE, MANDATES, LAYER, CHIPS, LIMITS titles, the tranche and pool lines, close quotes, references line).
- `build-card-0.py`, `build-card-6.py`, `build-why.py`, `build-title.py`: page text as Python strings.
- `build-onepage.py`: its own tightened wording.
- `build-text.py`: hardcoded recon-gap rows.
- `handoff/docs/asset-formulas.md`: the numbers that check-sync treats as a source.

**Fragile couplings to remove:**
- `build-deck.py` runs *part* of other scripts by splitting their source on a marker string (`split("HANDLE =")`, `split("MECHANISM =")`, `split("n = sum")`).
- About 30 hardcoded absolute paths (`/home/claude/v3`, `/home/claude/print`, `/home/claude/handoff/docs`, and the session scratchpad for deck output).
- Card HTML is both a hand-edited source and a build input; some pages are generated and then patched by string replacement (`build-whyme.py`, `build-disclosure.py`).
- The deck publishes through the Slides artifact, a step that can't run from the repo. The repo build writes slide HTML and `deck.json`, and publishing stays a manual or Claude step.

## Phase 0 · parity harness (first)

- [ ] Snapshot every current output into `baseline/`: slide HTML, card HTML + PNG, web HTML, print PDF, one-pager HTML + PNG, text edition.
- [ ] `check-parity.py`: compares extracted text exactly and images by pixel diff (a small threshold for font antialiasing). Exits non-zero on any change.
- [ ] Rule for every later step: **parity passes, or the diff is shown to the author and he approves it.**

## Phase A · build scripts into the repo

- [ ] A1 · One `config.py` with every path, relative to the repo root; replace all absolute paths. Deck output goes to `out/deck/`, not the scratchpad.
- [ ] A2 · Replace the source-splitting `exec` hacks with plain imports: move the shared constants into a module (`common.py`: colours, fonts, HANDLE, helpers such as `ul`, `body`, `emo`, `head`).
- [ ] A3 · One entry point, `build.py`, that runs the chain in order: cards → deck → fit → pages → web → checks → one-pager → text → print. It stops on the first failure. `build.py --only deck` for partial runs.
- [ ] A4 · `requirements.txt` (playwright, reportlab, pypdf, Pillow) and a README section: install, `playwright install chromium`, run.
- [ ] A5 · Fonts: bundle `fonts/` (Instrument Serif, JetBrains Mono and Source Sans 3 are all OFL; include the licence files) so renders don't depend on Google Fonts.
- [ ] A6 · **Comment policy (author decides, see Q1)**, applied before the first public push.
- [ ] A7 · Privacy sweep before pushing: the scripts, the docs and the handoff bundle. Checked 28 Sep: no email addresses, phone numbers or employer references in `v3/`, `print/` or `handoff/docs/`. Re-run just before the push.
- [ ] A8 · Layout: `build/` (scripts), `content/` (cards now, the content file later), `out/` (gitignored), `baseline/`, `archive/`. Retire `bulletize-cards.py` into `archive/`.
- [ ] A9 · Parity passes from a fresh clone, then push.

## Phase B · one content source

**Schema sketch** (YAML):
```yaml
hormuz-why:
  eyebrow: "Hormuz · why a commission"
  title: "Why a shared strait"
  items:
    - "Geography is king · the strait runs partly through Iranian territorial waters…"
    - text: "It has also proven it can’t impose its will on the Gulf · [[nowrap:the US and Gulf states contained the disruption, at high cost]]"
      text@text: "…plain variant for the text edition, only if it differs…"
  notes: "…"
  in: [deck, web, print, text]
```
- **Defaults plus variants** (`field@edition`), used only where the wording deliberately differs (the one-pager, the text edition's plain hyphen), never as silent copies.
- **One inline syntax:** `**bold**`, `[text](url)`, `[[nowrap:…]]`, `&nbsp;` handled in one place; each builder renders it for its format.
- **Layout stays in the builders:** emoji, `data-nudge`, fit-deck SKIP, figure geometry, per-slide sizes.

**Steps · one edition per step, parity after each:**
- [ ] B1 · Write an extractor that pulls the text **verbatim** from every place in the inventory into `content/accords.yaml`, keyed by slide/section id. No rewording. Record where each string came from.
- [ ] B2 · Report near-duplicates (the same idea worded differently in two places) to the author as a list. **Don't merge any without his ruling.**
- [ ] B3 · Text edition reads YAML (the simplest; proves the schema).
- [ ] B4 · Deck: `deck-text.py` and the inline text in `build-deck.py` move to YAML; `card_lists()` parsing goes away.
- [ ] B5 · Cards 1–6 and the generated pages are rendered from YAML plus templates (the hardest; the cards are hand-tuned HTML, so pixel parity matters).
- [ ] B6 · Web, print, one-pager.
- [ ] B7 · Shrink `check-sync.py` to a variant audit (lists every `@edition` override for review); keep `check-lists` and `check-positioned`.
- [ ] B8 · Archive the retired copies (`deck-text.py`, hand-written card HTML) under `archive/` with a MANIFEST line. **Delete nothing.**

## Open questions for the author

1. **Dated comments** (about 70 lines quoting you with timestamps, e.g. "author, 28 Sep 23:27"). Should they (a) stay in public as provenance, which fits the AI disclosure, (b) move to a CHANGELOG, or (c) stay in the private session logs only?
2. **YAML or JSON?** YAML is easier to hand-edit; JSON has no ambiguity.
3. Once cards render from YAML, **is the YAML the ratified source**, or do you keep ratifying the rendered cards?
4. Should the session logs and research docs (`handoff/docs/`) go in the repo, or stay private?
5. Timing: after the final pass, or only if the plan keeps being updated as the talks move?

## Out of scope

- Any wording change. This is plumbing only.
- New editions, redesigns, and the ~50-slide trim.
- Automating the Slides-artifact publish.
- The GitHub Pages site's own code (the ask buttons, the licence) beyond pointing it at `out/`.

## Repo-side notes (added 29 Sep 2026 by the code session)

How the plan meets the repo as it stands. Settle these before Phase A lands.

**Conflicts with how the repo works today**
1. **Published files stay at the root.** GitHub Pages serves `main` as is. `index.html`, `islamabad-accords.pdf` and `islamabad-accords.md` are at shared URLs, and the Ask buttons point the AI at the `.md` URL. If `out/` is gitignored, the build must copy those three back to the root, or Pages must switch to deploying from a GitHub Action. Pick one.
2. **The source of truth flips.** Today the Slides artifact is upstream and `deck/` is a copy (CLAUDE.md, "Syncing from the deck"). Once the repo builds the deck, the sync steps and the daily 08:50 sync routine would copy the artifact back over the repo's own output. Rewrite both (or pause the routine) in the same PR that moves the build in.
3. **The page wrapper stays repo-owned.** `build-slideshow.py` turns `deck/` into `index.html` and holds the Ask buttons, menu labels, `SLIDE_ALIASES` and the iOS fix. A3's chain should call it as its last step, never replace it with a chat copy.
4. **Slide ids stay stable.** B4 should key the YAML by the current slide ids, so shared links and the existing redirects keep working.

**Things that will bite**
5. **Pixel parity depends on the machine.** Font smoothing and emoji differ between the chat container, the code container and GitHub's runners; emoji most of all, since the deck now uses them everywhere. Make and compare the baseline in the same environment, ideally in CI. Bundled fonts (A5) help, but emoji still come from each machine's emoji font.
6. **Check the dependencies install.** `pypdf` crashed in the code container (a `cryptography` panic); the PDF was read with pdf.js instead. Confirm all four packages in `requirements.txt` install before CI relies on them.
7. **Git history is permanent.** The privacy sweep (A7) and the dated comments (Q1) must be settled before the first push; deleting later leaves it in history.
8. **Licences.** Scripts fall under the existing MIT `LICENSE`. `content/accords.yaml` and `baseline/` are the author's text and design, so `LICENSE-CONTENT.md` should list them under CC BY 4.0.
9. **Snapshot weight.** A baseline of PDFs and PNGs, re-committed on every approved change, grows the repo fast. Keep it to text plus a few key renders, or store it outside git.

**Suggested answers, for the author to confirm**
- Q2: YAML, with every string quoted (unquoted YAML turns `no` or `on` into booleans, and a colon in the text can break a line).
- Q3: the YAML. Ratifying the rendered cards keeps two sources.
- Q5: a quiet week; Phase A alone changes the process the daily sync depends on.
