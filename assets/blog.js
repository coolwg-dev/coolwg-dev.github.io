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
      const posts = await fetchJSON('posts/posts.json');
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
      const a = el('a',{href:'#', 'data-path': post.path}, titleText);
      a.addEventListener('click', (e)=>{ e.preventDefault(); loadPost(post); history.replaceState(null,'', '?post='+post.slug); });
      item.appendChild(a);
      if(post.date) item.appendChild(el('div',{class:'post-date'}, post.date));
      container.appendChild(item);
    });
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

      // fallback: fetch the HTML file
      const res = await fetch(post.path || post);
      if(!res.ok) throw new Error('Failed to load post');
      const html = await res.text();
      content.innerHTML = html;
      window.scrollTo({top:0, behavior:'smooth'});
    }catch(err){
      const errText = (window.i18nT && window.i18nT('blog.unable_load')) || '<p>Unable to load post.</p>';
      if(content) content.innerHTML = errText;
      console.error(err);
    }
  }

  if(document.getElementById('posts-list')){
    loadPosts();
  }

})();
