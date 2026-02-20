# How to Add a New Blog (Markdown)

This is a concise HOWTO for adding a new blog post in Markdown to this repository. It's a guide only — not an actual blog post.

- Content assets (images): put them alongside the post or under `assets/blog/<slug>/` (or alongside the MD file)
- The post (.md) itself should be put in `assets/blog/` (this repository includes a client-side renderer that
  parses Markdown into HTML in the browser, so you don't need a separate static-generation step). Do not put
  the post MD files under `public/[lang]/blog`.

## File name and slug
- Recommended filename: `your-slug.en.md` or `your-slug.es.md` or  `your-slug.language.md`, please use the same your-slug throughout all the languages, you should preferentially use the language of english as your slug
- Set `slug` in frontmatter to the desired URL path segment (e.g., `your-slug` → `/en/blog/your-slug`)

## Required frontmatter (example)
Place YAML frontmatter at the top of the file. Minimal example:

```yaml
---
title: "Your Post Title"
date: "2026-02-19"
slug: "your-post-slug"
lang: "en"
description: "Short summary for previews and SEO."
tags:
  - tag1
  - tag2
coverImage: "/assets/blog/your-post/cover.jpg"
draft: false
---
```
reminder: please do not add ```markdown at the start of a md, and also the tags should all be in english, but the title and the content should be in its own language, and there must be more than 3 parts in the content, and each part of the content should have more than 10 sentences. the content should be more academically and refer to some webstie online. Please use normal mark down langauge (e.g. #, ##, ###) to process the content instead of writing just partI partII.

Notes about runtime rendering:
- Place the `.md` file under `assets/blog/` so it is served by the site (example: `assets/blog/your-slug.en.md`).
- The client will look for a locale-specific filename (e.g. `your-slug.en.md`) or a generic `your-slug.md` and
  will parse the Markdown at runtime using a JS component (marked + DOMPurify). Frontmatter (the leading `---` YAML)
  is stripped before rendering so fields like `title` and `description` can be used by other tools but won't appear
  in the rendered body.

## Body content
- Write Markdown below the frontmatter (headings, lists, code blocks, images, etc.)
- Reference images via public paths (e.g., `/assets/...`) or relative paths depending on where you placed them
- Keep large assets in `src/assets/blog/<slug>/` or `public/assets/blog/<slug>/`

## Localization
- Use the same `slug` across locales if you want matching per-locale URLs

## Example minimal post

---
title: "My New Post"
date: "2026-02-19"
slug: "my-new-post"
lang: "en"
description: "A one-line overview."
tags: ["example"]
draft: false
---

Welcome to my new blog post. This is a short example.
```

## Commit and publish (recommended)

```bash
git add public/en/blog/your-file.md src/assets/blog/your-post/*
git commit -m "Add blog: your-post-slug"
```

## Next steps
- Optionally add a README link or a repo-level index to point automated tools / LLMs to this guide

---
Created as a repository guidance file for programmatic and manual reference.
