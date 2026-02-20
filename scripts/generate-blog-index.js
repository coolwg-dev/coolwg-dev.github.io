#!/usr/bin/env node
// Simple generator: scans assets/blog/*.md, reads YAML frontmatter (very small parser),
// and emits assets/blog/index.json grouping posts by slug and available locales.
const fs = require('fs');
const path = require('path');

const BLOG_DIR = path.join(__dirname, '..', 'assets', 'blog');
const OUT = path.join(BLOG_DIR, 'index.json');

function parseFrontMatter(s){
  if(!s.startsWith('---')) return {};
  const end = s.indexOf('\n---', 3);
  if(end === -1) return {};
  const block = s.slice(3, end).trim();
  const lines = block.split(/\n/);
  const out = {};
  for(const line of lines){
    const m = line.match(/^([a-zA-Z0-9_]+):\s*(.*)$/);
    if(m){
      const key = m[1];
      let val = m[2].trim();
      if(val.startsWith('"') && val.endsWith('"')) val = val.slice(1,-1);
      if(val.startsWith("'") && val.endsWith("'")) val = val.slice(1,-1);
      out[key] = val;
    }
  }
  return out;
}

function buildIndex(){
  const files = fs.readdirSync(BLOG_DIR).filter(f=>/\.md$/i.test(f));
  const posts = Object.create(null);
  for(const f of files){
    const full = path.join(BLOG_DIR, f);
    const raw = fs.readFileSync(full, 'utf8');
    const fm = parseFrontMatter(raw);
    // expected filename: slug.lang.md or slug.md
    const parts = f.split('.');
    let slug = parts[0];
    let lang = fm.lang || (parts.length>=3?parts[1]:'');
    if(!lang) lang = 'en';
    if(!posts[slug]) posts[slug] = { slug, date: fm.date || '', titles: {}, locales: {} };
    posts[slug].titles[lang] = fm.title || posts[slug].titles[lang] || '';
    posts[slug].locales[lang] = '/assets/blog/' + f.replace(/\\/g,'/');
    if(fm.date && !posts[slug].date) posts[slug].date = fm.date;
  }
  return Object.values(posts).sort((a,b)=> (b.date||'').localeCompare(a.date||''));
}

function main(){
  try{
    const idx = buildIndex();
    fs.writeFileSync(OUT, JSON.stringify(idx, null, 2), 'utf8');
    console.log('Wrote', OUT);
  }catch(e){
    console.error(e);
    process.exit(1);
  }
}

if(require.main === module) main();
