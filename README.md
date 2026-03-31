# coolwg-dev.github.io

Static GitHub Pages site for the `coolwg-dev` organization.

This repository now serves a **pure static site** from the `docs/` folder using only HTML, CSS, and (optionally) a small Node script for sitemap generation. No Astro or other frontend frameworks are used.

## Quick start — preview locally

For quick checks, you can serve the `docs/` folder locally using a simple HTTP server from the repository root:

- **Python** (built-in): `python -m http.server 8000`
- **Node.js** (http-server): `npx http-server -p 8000`

Then open http://localhost:8000/docs/ in your browser to view the site.

Alternatively, you can `cd docs` and run the same commands there, then open http://localhost:8000/.

## Deploy

GitHub Pages should be configured to publish from the `docs/` directory on the `main` branch. Push changes to `main`, and the site will deploy automatically (once Pages is enabled in the repository settings).

## Project Structure (static site)

- `docs/index.html` — main landing page
- `docs/blog/index.html` — blog index page with links to all posts
- `docs/blog/*/index.html` — individual blog posts (one folder per post)
- `docs/blog/_post-template.html` — copy-and-edit template for creating new blog posts
- `docs/assets/styles.css` — shared site styling
- `docs/assets/images/` — image assets
- `docs/assets/blog/` — blog-specific images (e.g., cover graphics)
- `robots.txt` — crawler directives
- `sitemap.xml` — sitemap (can be regenerated with the script below)
- `scripts/generate-sitemap.js` — helper to create `sitemap.xml` from HTML files under `docs/`

## Adding a new blog post

1. Create a new folder under `docs/blog/`, for example `docs/blog/my-new-post/`.
2. Copy the template file:
	- `docs/blog/_post-template.html` → `docs/blog/my-new-post/index.html`
3. Edit `docs/blog/my-new-post/index.html`:
	- Update the `<title>` in the `<head>`.
	- Update the `<meta name="description">` (and optionally `keywords` and `og:image`).
	- Update the `<h1>` and the date / language line in the `<header>`.
	- Replace the placeholder `<article>` content with your actual HTML content.
4. Update the blog index at `docs/blog/index.html`:
	- Add a new entry that links to `/blog/my-new-post/` and includes title, date, and a short 1–2 sentence excerpt.

All changes are manual edits to HTML files; no build step is required.

## Generating sitemap.xml

A small Node.js script is included to generate `sitemap.xml` automatically. Run it from the repository root:

```bash
node scripts/generate-sitemap.js
```

The script scans `.html` files under the `docs/` directory, uses file modification times for `<lastmod>`, and writes `sitemap.xml` at the repo root.


