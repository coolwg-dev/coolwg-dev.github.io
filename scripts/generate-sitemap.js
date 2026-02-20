#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// Configuration
const SITE_ROOT = 'https://coolwg-dev.github.io/';
const ROOT_DIR = process.cwd();
const OUTPUT = path.join(ROOT_DIR, 'sitemap.xml');

function isHtml(file) {
  return file.toLowerCase().endsWith('.html');
}

function walkDir(dir, fileList = []) {
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const full = path.join(dir, item.name);
    if (item.isDirectory()) {
      walkDir(full, fileList);
    } else if (item.isFile() && isHtml(item.name)) {
      // Exclude sitemap.xml itself
      if (path.basename(full).toLowerCase() === 'sitemap.xml') continue;
      fileList.push(full);
    }
  }
  return fileList;
}

function fileUrlFromPath(filePath) {
  // Make path relative to ROOT_DIR
  let rel = path.relative(ROOT_DIR, filePath).replace(/\\/g, '/');
  if (rel === 'index.html') rel = '';
  return SITE_ROOT + rel;
}

function formatDate(date) {
  return date.toISOString();
}

function generate() {
  const files = walkDir(ROOT_DIR);
  const urls = files.map(file => {
    const stats = fs.statSync(file);
    return {
      loc: fileUrlFromPath(file),
      lastmod: formatDate(stats.mtime)
    };
  });

  const header = `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;

  const body = urls.map(u => {
    return `  <url>\n    <loc>${u.loc}</loc>\n    <lastmod>${u.lastmod}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.5</priority>\n  </url>`;
  }).join('\n');

  const xml = header + body + '\n</urlset>\n';

  fs.writeFileSync(OUTPUT, xml, 'utf8');
  console.log('Wrote', OUTPUT);
}

if (require.main === module) {
  try {
    generate();
  } catch (err) {
    console.error('Error generating sitemap:', err);
    process.exit(1);
  }
}
