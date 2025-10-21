# coolwg-dev.github.io

Placeholder GitHub Pages site for the `coolwg-dev` organization.

This site now uses a Jekyll theme: `jekyll-theme-slate` (a grey theme supplied by GitHub Pages).

Quick start — preview locally with Jekyll (recommended):

1. Install Ruby and Bundler if you don't have them. On Windows, using RubyInstaller is recommended.
2. From the repository root install dependencies and serve locally:

```powershell
gem install bundler
bundle install
bundle exec jekyll serve --host 127.0.0.1 --port 4000
```

Open http://127.0.0.1:4000 in your browser.

If you prefer a lightweight file server for quick checks you can still use:

- Python: `python -m http.server 8000`
- Node (http-server): `npx http-server -p 8000`

Deploy:

- This repository is configured for GitHub Pages. Push to the `main` branch and enable GitHub Pages in repository settings if not already enabled.

Files added:

- `index.html` — the placeholder landing page
- `assets/styles.css` — simple styling
- `README.md` — this file

Next steps:

- Add organization content, navigation, and pages.
- Optionally add an automated CI/CD workflow to validate and deploy the site.
