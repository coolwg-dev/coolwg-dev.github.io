## Plan: Migrate Astro Site to Pure Static HTML/CSS/JS

TL;DR: Treat the existing docs/ output as the new source of truth, strip out all Astro runtime artifacts, rewrite or simplify a few key HTML files, and document a very simple "copy this template" workflow for adding new blog posts directly as HTML. No build step or framework will remain; GitHub Pages will just serve the docs/ folder as-is.

**Steps**

1. **Confirm deployment and target structure**
   1. Verify in GitHub Pages settings that the publish directory is docs/ (expected given current structure).
   2. Decide that, post-migration, docs/ is no longer a build artifact but the hand-edited source of the live site.
   3. Optionally keep a backup branch/tag of the current Astro-based setup in case you ever want to revert.

2. **Normalize static assets and CSS**
   1. Compare public/assets/styles.css, src/assets/styles.css, and docs/assets/styles.css; choose one as canonical (recommended: keep docs/assets/styles.css since it already works in production).
   2. Ensure all HTML files in docs/ reference the chosen CSS via a simple <link rel="stylesheet" href="/assets/styles.css"> tag.
   3. Ensure images, favicon, and other assets live under docs/assets/ (copy from public/assets/ if needed so everything the site needs is under docs/).

3. **Strip Astro runtime from generated HTML**
   1. In all HTML files under docs/ (index.html, blog/index.html, blog/*/index.html, post/index.html):
      - Remove script tags and link tags that reference the _astro/ directory (modulepreload + JS bundles).
      - Optionally remove data-astro-* attributes and any Astro-specific classnames if you want cleaner markup (not functionally required).
   2. Delete the docs/_astro/ directory entirely.
   3. Open docs/index.html in a browser to confirm the page still renders and looks correct using only the static CSS.

4. **Migrate blog content to a manual HTML workflow**
   1. For each existing blog post directory under docs/blog/ (e.g., choosing-your-frontend-languagecn, choosing-your-frontend-languageen, etc.):
      - Treat the current docs/blog/.../index.html file as the canonical version of the content going forward.
      - Optionally simplify the markup: keep a clean <article> structure with headings, dates, and paragraphs, and drop any extraneous wrapper divs or Astro-specific attributes.
   2. Once the docs/blog/.../index.html versions look good and are easy to understand/edit by hand, you can consider the original markdown files in src/content/blog/ as archival only and later delete them.
   3. Decide whether to keep the current slug pattern {baseSlug}-{lang} (recommended for existing posts to avoid breaking links) even though you’re OK with changes; for new posts, you can pick any descriptive folder name that keeps things readable.

5. **Simplify and fix the blog index page**
   1. Open docs/blog/index.html and:
      - Remove any Astro-specific script tags or attributes left over from the build.
      - Reduce it to a simple static list/grid of posts: each entry includes title, language label, date, 1–2 sentence excerpt, and a link to the corresponding docs/blog/{slug}/ index.html.
   2. Reorder the posts manually in the HTML so the newest ones appear first (since there’s no build step to auto-sort).
   3. Make sure there is a clear way to see that each post has multiple language versions (e.g., group cards by baseSlug or add language badges in the link text).
   4. Update the home page (docs/index.html) so the "Blog" link points to /blog/ and any featured posts sections match whatever structure you chose on the blog index.

6. **Create a reusable blog-post HTML template for future posts**
   1. Pick one of the cleaned-up blog post HTML files as the basis for a template.
   2. Save a copy as docs/blog/_post-template.html (or docs/templates/blog-post.html) containing:
      - A complete <html> skeleton with <head> metadata fields (title, description, og tags) wired to obvious placeholder text.
      - The shared header/nav/footer structure that matches the rest of your site.
      - A main <article> section with placeholder headings, date, and paragraphs.
   3. Add comments in the template marking what must be changed when creating a new post: page title, meta description, canonical URL (if you use it), published date, language label, and the main article body.
   4. Define a simple manual workflow for adding a post:
      - Copy docs/blog/_post-template.html to a new folder docs/blog/new-post-slug/ as index.html.
      - Edit the head metadata and article content.
      - Add a corresponding entry to docs/blog/index.html (title, date, excerpt, link, language tag).
      - Optionally, add links between language variants if you keep multiple languages per post.

7. **Remove Astro-specific source and build config**
   1. Once you are satisfied that docs/ has clean, editable HTML for all pages you care about:
      - Remove astro.config.mjs.
      - Remove the entire src/ directory (layouts, pages, content, utils) after you’re comfortable you no longer need the Astro source.
      - Remove the .astro/ cache directory if present.
   2. Remove Node-related files tied to Astro:
      - Delete package.json and package-lock.json if they only exist for Astro.
      - Delete node_modules/.
   3. Keep scripts/generate-sitemap.js if you still want automated sitemap generation; it uses only Node core modules and doesn’t introduce a runtime framework.

8. **Update project documentation and housekeeping**
   1. Update README.md to describe the new, framework-free setup:
      - Explain that docs/ is the source and publish directory.
      - Document the “add a new blog post” workflow based on copying the template and editing docs/blog/index.html.
      - Document how to run scripts/generate-sitemap.js with node if you want to regenerate sitemap.xml.
   2. Optionally move any now-unused files (e.g., locales JSON under public/assets/locales/) into an archive folder or delete them if you don’t plan to use JS-based i18n.
   3. Ensure robots.txt and sitemap.xml in the repo are consistent with the actual pages under docs/ (either keep them static or rely purely on the generated sitemap from the script).

9. **Verification and polish**
   1. Open docs/index.html, docs/blog/index.html, and each docs/blog/*/index.html directly in a browser to confirm:
      - Layout and styling match your expectations.
      - All navigation links work (home ↔ blog ↔ posts).
      - There are no 404s for CSS or image assets.
   2. If you keep scripts/generate-sitemap.js, run it and inspect the resulting sitemap.xml to ensure it includes all blog posts and key pages.
   3. Push the changes to GitHub and verify GitHub Pages serves the updated docs/ correctly (no references to /_astro/, no console errors, all pages load with only static HTML/CSS/JS).

**Relevant files**
- docs/index.html — Home page; becomes manually edited static HTML.
- docs/blog/index.html — Blog index; manually maintained list of posts.
- docs/blog/*/index.html — Individual posts; canonical content in plain HTML.
- docs/assets/styles.css — Canonical stylesheet for the entire site.
- docs/_astro/ — Astro runtime bundle directory to delete.
- scripts/generate-sitemap.js — Optional Node script to regenerate sitemap.xml after changes.
- README.md — Update to describe new static architecture and blog workflow.
- astro.config.mjs, src/**, .astro/, package.json, package-lock.json, node_modules/ — Astro-related files and directories to remove once migration is complete.

**Verification**
1. Manually browse all key HTML pages under docs/ in a local browser and confirm layout and navigation using only static assets.
2. Check the browser dev tools network tab to verify there are no requests to /_astro/ or other missing script bundles.
3. Regenerate sitemap.xml with scripts/generate-sitemap.js (if desired) and confirm URLs match the structure in docs/.
4. After pushing to GitHub, confirm the live site works and URLs behave as expected from an incognito browser session.

**Decisions**
- You chose to add new blogs by writing HTML files directly under docs/blog/... with no build step, so the plan avoids any markdown-to-HTML generator or bundler.
- Although you’re OK changing URLs, the plan keeps existing blog slugs for current posts to avoid breaking links; for new posts you can choose any simple, descriptive folder name.
- Node is used only optionally for running scripts/generate-sitemap.js; no framework or bundler remains in the runtime or deployment path.

**Further Considerations**
1. If, in the future, maintaining the blog index by hand becomes tedious, you could introduce a tiny client-side JS snippet on docs/blog/index.html that reads a simple JSON registry of posts and renders the list dynamically—still framework-free and without a separate build step.
2. If you later decide to drop multi-language posts or change how they are organized, you can simplify docs/blog/ to a single language per post and remove unused language variants without changing the underlying static architecture.
3. For long-term maintainability, you may want to adopt a naming convention for post folders and a simple checklist (title, date, language, excerpt, link) to follow whenever you add a new post.