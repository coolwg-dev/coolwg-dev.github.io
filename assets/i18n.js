// Simple i18n loader for static site
(function(){
  const defaultLang = 'en';
  const select = document.getElementById('lang-select');

  function getLangFromUrl(){
    try{ return new URLSearchParams(location.search).get('lang') || null; }catch(e){ return null; }
  }

  function getSavedLang(){
    return localStorage.getItem('lang') || null;
  }

  function saveLang(lang){
    localStorage.setItem('lang', lang);
  }

  function fetchLocale(lang){
    return fetch(`/assets/locales/${lang}.json`).then(r => {
      if(!r.ok) throw new Error('Locale not found');
      return r.json();
    });
  }

  function getNested(obj, key){
    return key.split('.').reduce((o,k)=> (o && o[k]!==undefined)? o[k] : undefined, obj);
  }

  function replaceTextNodes(el, text){
    for(const node of el.childNodes){
      if(node.nodeType === Node.TEXT_NODE && node.textContent.trim().length){
        node.textContent = text;
        return;
      }
    }
    el.appendChild(document.createTextNode(text));
  }

  function translate(translations){
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const value = getNested(translations, key) || '';
      const replaced = value.replace(/\{\{?year\}?\}/g, new Date().getFullYear());
      if(replaced && el.childNodes.length){
        replaceTextNodes(el, replaced);
      } else {
        el.textContent = replaced;
      }
    });

    if(translations && translations.title){
      document.title = translations.title;
    }
    try{
      window.__translations = translations || {};
      window.i18nT = function(key){ return getNested(window.__translations || {}, key) || ''; };
    }catch(e){ }
  }

  function setLang(lang){
    fetchLocale(lang).then(translations => {
      translate(translations);
      document.documentElement.lang = lang;
      saveLang(lang);
      window.__lang = lang;
      if(select) select.value = lang;
      try{
        const params = new URLSearchParams(location.search);
        params.set('lang', lang);
        const newUrl = location.pathname + (params.toString() ? ('?' + params.toString()) : '') + location.hash;
        history.replaceState(null, '', newUrl);
      }catch(e){ }
      try{
        const ev = new CustomEvent('i18n:ready', { detail: { lang } });
        document.dispatchEvent(ev);
      }catch(e){ }
    }).catch(err => {
      console.warn('i18n: failed to load', lang, err);
    });
  }

  const saved = getSavedLang();
  const urlLang = getLangFromUrl();
  const browser = (navigator.languages && navigator.languages[0]) || navigator.language || defaultLang;
  const start = urlLang || saved || browser.split('-')[0] || defaultLang;

  if(select){
    select.addEventListener('change', (e)=> setLang(e.target.value));
  }

  window.addEventListener('load', ()=> setTimeout(()=> setLang(start), 10));

})();
