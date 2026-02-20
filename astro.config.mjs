import { defineConfig } from 'astro/config';

// Set the production site URL for Astro (used for absolute URLs and sitemap)
export default defineConfig({
  site: 'https://coolwg-dev.github.io',
  outDir: 'docs',
});

// name: Build and deploy site
// on:
//   push:
//     branches: [ main ]
// jobs:
//   build-deploy:
//     runs-on: ubuntu-latest
//     steps:
//       - uses: actions/checkout@v4
//       - uses: actions/setup-node@v4
//         with:
//           node-version: 18
//       - run: npm ci
//       - run: npm run build
//       - name: Deploy to GitHub Pages
//         uses: peaceiris/actions-gh-pages@v3
//         with:
//           github_token: ${{ secrets.GITHUB_TOKEN }}
//           publish_dir: ./docs
