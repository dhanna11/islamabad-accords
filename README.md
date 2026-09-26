# The Islamabad Accords · website

- `index.html`: the slideshow. Click Next and Previous, use the arrow keys or the space bar, swipe on a phone, or click the left or right half of a slide. Each slide has its own link, for example `#nuclear`.
- `islamabad-accords.pdf`: the PDF edition, linked from the slideshow's PDF button.
- `build-slideshow.py`: rebuilds `index.html` from the published deck (deck.json plus slides/*.html). Run it after the deck changes, then copy in the fresh PDF.

## Publish on GitHub Pages
1. Create a repository, for example `islamabad-accords`, and add `index.html` and `islamabad-accords.pdf` at the top level.
2. In the repository, go to Settings → Pages. Under Source, pick "Deploy from a branch", then choose `main` and `/ (root)`.
3. After a minute the site is at `https://<your-username>.github.io/islamabad-accords/`.

## A custom subdomain (optional)
1. In Settings → Pages → Custom domain, enter for example `accords.virtuouscityvision.com`. This adds a `CNAME` file.
2. At your DNS provider, add a CNAME record from `accords` to `<your-username>.github.io`.
3. Once the certificate is issued, tick "Enforce HTTPS".

The only thing the page loads from outside is its fonts, from Google Fonts.

## License
- **Text and design** (the deck, the slides, the PDF and the plain-text edition): © 2026 David Hanna Jr., [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE-CONTENT.md`. Quoted material and sources belong to their authors.
- **Build scripts and code** (`build-slideshow.py`, `tests/`, `.github/`, and the page wrapper around the slides): [MIT](LICENSE).
