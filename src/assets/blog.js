// Minimal blog component: fetches blog/posts/posts.json and renders list
(function(){
  async function fetchJSON(url){
    const res = await fetch(url);
    if(!res.ok) throw new Error('Failed to fetch '+url);
    return res.json();
  }

  function el(tag, attrs, ...children){
    const e = document.createElement(tag);
    if(attrs) Object.entries(attrs).forEach(([k,v])=> e.setAttribute(k,v));
    children.forEach(c=>{ if(typeof c==='string') e.appendChild(document.createTextNode(c)); else if(c) e.appendChild(c)});
    return e;
  }

  async function loadPosts(){
    try{
      let posts = null;
      if(window.BLOG_POSTS && Array.isArray(window.BLOG_POSTS)){
        posts = window.BLOG_POSTS;
      } else {
        // Try a conventional assets manifest first (recommended):
        // /assets/blog/index.json
        try{
          posts = await fetchJSON('/assets/blog/index.json');
        }catch(e){
          // Fallback to legacy location if present (keeps backward compatibility)
          try{
            posts = await fetchJSON('posts/posts.json');
          }catch(e2){
            posts = null;
          }
        }
      }

      if(!posts || !Array.isArray(posts)){
        const node = document.getElementById('posts-list');
        if(node) node.textContent = (window.i18nT && window.i18nT('blog.list_error')) || 'Could not load posts.';
        console.error('No posts index found');
        return;
      }
      renderList(posts);
      const params = new URLSearchParams(location.search);
      const slug = params.get('post');
      if(slug){
        const p = posts.find(x => x.slug===slug);
        if(p) loadPost(p);
      }
    }catch(err){
      const msg = (window.i18nT && window.i18nT('blog.list_error')) || 'Could not load posts.';
      const node = document.getElementById('posts-list');
      if(node) node.textContent = msg;
      console.error(err);
    }
  }

  function renderList(posts){
    const container = document.getElementById('posts-list');
    container.innerHTML = '';
    posts.forEach(post=>{
      const item = el('div',{class:'post-item'});
      // prefer localized title if available
      const localizedTitle = (window.i18nT && post.titleKey) ? window.i18nT(post.titleKey) : '';
      const titleText = localizedTitle || post.title || post.slug;
      // include current lang in the link so post pages keep the selected language
      const currentLang = window.__lang || (new URLSearchParams(location.search).get('lang')) || localStorage.getItem('lang') || '';
      const langParam = currentLang ? '&lang=' + encodeURIComponent(currentLang) : '';
      const a = el('a',{href: 'post.html?post='+encodeURIComponent(post.slug) + langParam, 'data-path': post.path}, titleText);
      item.appendChild(a);
      if(post.date) item.appendChild(el('div',{class:'post-date'}, post.date));
      container.appendChild(item);
    });
  }

  // If we're on a dedicated post page (post.html), load the requested post
  if(document.getElementById('post-content') && !document.getElementById('posts-list')){
    (async function(){
      try{
        let posts = null;
        if(window.BLOG_POSTS && Array.isArray(window.BLOG_POSTS)){
          posts = window.BLOG_POSTS;
        } else {
          try{
            posts = await fetchJSON('/assets/blog/index.json');
          }catch(e){
            try{
              posts = await fetchJSON('posts/posts.json');
            }catch(e2){
              posts = null;
            }
          }
        }

        if(!posts || !Array.isArray(posts)){
          const content = document.getElementById('post-content');
          if(content) content.innerHTML = '<p>Unable to load posts index.</p>';
          return;
        }

        const params = new URLSearchParams(location.search);
        const slug = params.get('post');
        const lang = params.get('lang') || (window.__lang) || localStorage.getItem('lang') || '';
        if(lang) window.__lang = lang;
        if(slug){
          const p = posts.find(x => x.slug===slug);
          if(p) loadPost(p);
        }
      }catch(err){
        console.error('Failed to load posts for post page', err);
        const content = document.getElementById('post-content');
        if(content) content.innerHTML = '<p>Unable to load posts index.</p>';
      }
    })();
  }

  async function loadPost(post){
    const content = document.getElementById('post-content');
    const loadingText = (window.i18nT && window.i18nT('blog.loading')) || 'Loading...';
    if(content) content.innerHTML = loadingText;
    try{
      // prefer localized post content if available via translation keys
      if(post && post.contentKey && window.i18nT){
        const localized = window.i18nT(post.contentKey);
        if(localized && localized.trim()){
          content.innerHTML = localized;
          window.scrollTo({top:0, behavior:'smooth'});
          return;
        }
      }

      // Try a set of candidate URLs (HTML or Markdown). This enables placing
      // Markdown files in `assets/blog/` and having them rendered client-side
      // without a static generation step.
      async function tryFetchText(url){
        try{
          const res = await fetch(url);
          if(!res.ok) return null;
          const text = await res.text();
          return {url, text, ok: true};
        }catch(e){
          return null;
        }
      }

      function stripYAMLFrontMatter(s){
        if(!s) return s;
        if(s.startsWith('---')){
          const idx = s.indexOf('\n---', 3);
          if(idx !== -1) return s.slice(idx+4).trim();
        }
        return s;
      }

      const lang = window.__lang || (new URLSearchParams(location.search).get('lang')) || '';
      const candidates = [];
      if(post.path) candidates.push(post.path);
      if(post.path && /\.html?$/i.test(post.path)) candidates.push(post.path.replace(/\.html?$/i, '.md'));
      // Prefer MD in assets/blog relative to the blog page
      if(post.slug){
        if(lang) candidates.push('../assets/blog/' + post.slug + '.' + lang + '.md');
        candidates.push('../assets/blog/' + post.slug + '.md');
      }
      // Also try a root-level assets path (in case the site is served from root)
      if(post.slug){
        if(lang) candidates.push('/assets/blog/' + post.slug + '.' + lang + '.md');
        candidates.push('/assets/blog/' + post.slug + '.md');
      }

      let loaded = false;
      for(const url of candidates){
        if(!url) continue;
        const result = await tryFetchText(url);
        if(!result) continue;
        const txt = result.text;
        const isMarkdown = /\.md$/i.test(result.url) || /^---\n/.test(txt) || /(^|\n)#\s+/.test(txt);
        if(isMarkdown && window.marked){
          const body = stripYAMLFrontMatter(txt);
          const parsed = window.marked.parse(body);
          const safe = (window.DOMPurify && window.DOMPurify.sanitize) ? window.DOMPurify.sanitize(parsed) : parsed;
          if(content) content.innerHTML = safe;
          window.scrollTo({top:0, behavior:'smooth'});
          loaded = true;
          break;
        } else {
          // treat as pre-rendered HTML
          if(content) content.innerHTML = txt;
          window.scrollTo({top:0, behavior:'smooth'});
          loaded = true;
          break;
        }
      }

      if(!loaded){
        throw new Error('No post found in candidate locations');
      }
    }catch(err){
      const errText = (window.i18nT && window.i18nT('blog.unable_load')) || '<p>Unable to load post.</p>';
      if(content) content.innerHTML = errText;
      console.error(err);
    }
  }

  if(document.getElementById('posts-list')){
    loadPosts();
  }

  // Re-run loading when translations become available so titles/content update
  try{
    document.addEventListener('i18n:ready', function(){
      if(document.getElementById('posts-list')){
        loadPosts();
      }
      if(document.getElementById('post-content') && !document.getElementById('posts-list')){
        const params = new URLSearchParams(location.search);
        const slug = params.get('post');
        const lang = params.get('lang') || window.__lang || localStorage.getItem('lang') || '';
        if(lang) window.__lang = lang;
        if(slug){
          fetchJSON('posts/posts.json').then(posts => {
            const p = posts.find(x => x.slug===slug);
            if(p) loadPost(p);
          }).catch(err => console.error(err));
        }
      }
    });
  }catch(e){ /* ignore environments without CustomEvent support */ }

})();
