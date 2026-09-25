# The Islamabad Accords · website repo

A static site: a click-through slideshow of the author's deck, plus the PDF edition. No framework, no build server.

## Files
- `index.html`: the slideshow, one self-contained page. It loads only Google Fonts from outside.
- `islamabad-accords.pdf`: the PDF edition, linked from the slideshow's PDF button.
- `deck/`: the deck export the slideshow is built from (`deck.json` for slide order and sections, `slides/*.html` for one slide each). This is the source. Do not hand-edit `index.html`.
- `build-slideshow.py`: regenerates `index.html` (and `preview.html`) from `deck/`. It needs only Python 3.
- `README.md`: the human steps for GitHub Pages and a custom domain.

## Tasks
### First-time setup
1. `git init`, commit everything except `preview.html`, and create a public GitHub repo, e.g. `gh repo create islamabad-accords --public --source=. --push`.
2. Turn on Pages from the main branch root:
   `gh api -X POST repos/{owner}/islamabad-accords/pages -f "source[branch]=main" -f "source[path]=/"`
3. Wait for the first deploy (`gh api repos/{owner}/islamabad-accords/pages/builds/latest`) and open `https://{owner}.github.io/islamabad-accords/`.
4. Optional custom domain: ask the author which domain to use first (one option floated: `accords.virtuouscityvision.com`). Then write it to a `CNAME` file, commit, and tell him the DNS record to add (a CNAME from the subdomain to `{owner}.github.io`). Enforce HTTPS once the certificate is issued.

### Updating after the deck changes
1. Replace `deck/deck.json` and `deck/slides/` with the new export, and `islamabad-accords.pdf` with the new PDF.
2. Run `python3 build-slideshow.py`.
3. Open `index.html` locally and step through a few slides, then commit and push.

## Rules
- The words on the slides are the author's. Never rewrite slide text here. Content changes happen upstream in the deck, then get re-exported.
- Keep the site static and self-contained. Don't add trackers, analytics or third-party scripts without asking.
- Every slide has a stable link (`index.html#<slide-id>`). Don't rename slide ids casually, since people may have shared them.
