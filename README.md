# coolwg-dev.github.io

Static GitHub Pages site for the `coolwg-dev` organization.

This is a simple static website with HTML, CSS, and JavaScript.

## Quick start — preview locally

For quick checks, you can serve the site locally using a simple HTTP server:

- **Python** (built-in): `python -m http.server 8000`
- **Node.js** (http-server): `npx http-server -p 8000`

Open http://localhost:8000 in your browser to view the site.

## Deploy

This repository is configured for GitHub Pages. Push changes to the `main` branch, and the site will automatically deploy if GitHub Pages is enabled in the repository settings.

## Project Structure

- `index.html` — the main landing page
- `assets/main.js` — JavaScript functionality
- `assets/styles.css` — site styling
- `assets/images/` — image assets
- `README.md` — this file
- `scripts/generate-sitemap.js` — helper to create `sitemap.xml` from HTML files

## Generating sitemap.xml

A small Node.js script is included to generate `sitemap.xml` automatically. Run it from the repository root:

```bash
node scripts/generate-sitemap.js
```

The script scans `.html` files in the project root (and subfolders), uses file modification times for `<lastmod>`, and writes `sitemap.xml` at the repo root.


