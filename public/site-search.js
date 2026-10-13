/* Exam Darpan global soft-search */
(function(){
  var style=document.createElement('style');
  style.textContent=".ed-global-search{position:relative;flex:1 1 360px;min-width:0;max-width:520px;margin-left:auto;z-index:80}.ed-global-search .ed-search-box{position:relative;display:flex;align-items:center;gap:9px;background:#fff;border:1px solid #dbe4f0;border-radius:15px;padding:0 14px;box-shadow:0 5px 18px rgba(15,23,42,.09);transition:border-color .18s,box-shadow .18s}.ed-global-search .ed-search-box:focus-within{border-color:#3b82f6;box-shadow:0 0 0 4px rgba(59,130,246,.13),0 8px 24px rgba(15,23,42,.1)}.ed-global-search .ed-search-icon{font-size:22px;color:#64748b;line-height:1}.ed-global-search input{width:100%;min-width:0;height:48px;border:0!important;outline:0!important;background:transparent!important;color:#172033!important;font-size:13px!important;font-weight:600;padding:0!important;box-shadow:none!important}.ed-search-results{position:absolute;top:calc(100% + 8px);left:0;right:0;display:none;max-height:min(65vh,430px);overflow:auto;background:#fff;border:1px solid #dbe4f0;border-radius:14px;box-shadow:0 18px 48px rgba(15,23,42,.2);padding:6px;z-index:9999}.ed-search-results.is-open{display:block}.ed-search-result{display:block;padding:11px 12px;border-radius:9px;color:#172033!important;text-decoration:none!important;line-height:1.4}.ed-search-result:hover,.ed-search-result:focus{background:#eff6ff;outline:0}.ed-search-result strong{display:block;font-size:12px;font-weight:800}.ed-search-result small{display:block;margin-top:4px;color:#64748b;font-size:10px}.ed-search-empty{padding:14px 12px;color:#64748b;font-size:12px}.ed-search-hint{padding:7px 12px;color:#94a3b8;font-size:9px;border-top:1px solid #eef2f7}@media(max-width:760px){.header .head{flex-wrap:wrap!important;align-items:center!important}.ed-global-search{order:3;flex:1 0 100%;max-width:none;margin:4px 0 2px}.ed-global-search .ed-search-box{border-radius:12px}.ed-global-search input{height:42px;font-size:12px!important}.ed-search-results{max-height:55vh}}";
  document.head.appendChild(style);
  function esc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
  function cleanSlug(v){return String(v||'').replace(/^\/+/,'').replace(/\.html$/,'');}
  function init(){
    var head=document.querySelector('.header .head');
    if(!head)return;
    var wrap=head.querySelector('.ed-global-search');
    var old=head.querySelector('.search input, #searchInput, input[type=\"search\"]');
    if(!wrap){
      wrap=document.createElement('div');wrap.className='ed-global-search';
      wrap.innerHTML='<div class=\"ed-search-box\"><span class=\"ed-search-icon\" aria-hidden=\"true\">⌕</span><input type=\"search\" aria-label=\"Search Exam Darpan articles\" autocomplete=\"off\" placeholder=\"भर्ती, Result, Admit Card या Syllabus खोजें...\"></div><div class=\"ed-search-results\" role=\"listbox\" aria-label=\"Search suggestions\"></div>';
      if(old){
        var oldBox=old.closest('.search');
        if(oldBox){oldBox.parentNode.insertBefore(wrap,oldBox);wrap.querySelector('input').replaceWith(old);oldBox.remove();}
        else{wrap.querySelector('input').replaceWith(old);head.appendChild(wrap);}
        old.removeAttribute('oninput');old.removeAttribute('id');old.setAttribute('type','search');old.setAttribute('autocomplete','off');old.setAttribute('placeholder','भर्ती, Result, Admit Card या Syllabus खोजें...');old.classList.add('ed-search-input');
      }else{
        var brand=head.querySelector('.brand'), button=head.querySelector('.btn');
        if(button)head.insertBefore(wrap,button);else if(brand&&brand.nextSibling)head.insertBefore(wrap,brand.nextSibling);else head.appendChild(wrap);
      }
    }
    var input=wrap.querySelector('input'), results=wrap.querySelector('.ed-search-results');
    if(!input||!results)return;
    var posts=[],active=-1;
    function close(){results.classList.remove('is-open');active=-1;}
    function render(){
      var q=input.value.trim().toLocaleLowerCase();
      if(q.length<2){results.innerHTML='';close();return;}
      var matches=posts.map(function(p){
        var title=String(p.title||'').toLocaleLowerCase(),cat=String(p.category||'').toLocaleLowerCase();
        var extra=String(p.excerpt||p.description||'').toLocaleLowerCase()+' '+String(p.tags||'').toLocaleLowerCase();
        return {p:p,score:(title.indexOf(q)>=0?5:0)+(cat.indexOf(q)>=0?3:0)+(extra.indexOf(q)>=0?1:0)};
      }).filter(function(x){return x.score>0;}).sort(function(a,b){return b.score-a.score;}).slice(0,7).map(function(x){return x.p;});
      if(!matches.length){results.innerHTML='<div class=\"ed-search-empty\">इस शब्द से कोई article नहीं मिला। दूसरा keyword try करें।</div>';results.classList.add('is-open');return;}
      results.innerHTML=matches.map(function(p,i){
        var href='/'+cleanSlug(p.slug);
        return '<a class=\"ed-search-result\" role=\"option\" data-index=\"'+i+'\" href=\"'+esc(href)+'\"><strong>'+esc(p.title||'Latest update')+'</strong><small>'+esc(p.category||'Exam Darpan')+(p.publishedAt?' · '+esc(String(p.publishedAt).slice(0,10)):'')+'</small></a>';
      }).join('')+'<div class=\"ed-search-hint\">↑ ↓ से चुनें · Enter दबाकर खोलें</div>';
      results.classList.add('is-open');active=-1;
    }
    input.addEventListener('input',render);input.addEventListener('focus',render);
    input.addEventListener('keydown',function(e){
      var links=Array.prototype.slice.call(results.querySelectorAll('.ed-search-result'));
      if(e.key==='Escape'){close();return;}
      if(e.key==='ArrowDown'&&links.length){e.preventDefault();active=(active+1)%links.length;links.forEach(function(a,i){a.classList.toggle('is-active',i===active);});links[active].focus();return;}
      if(e.key==='Enter'){if(links.length){e.preventDefault();var target=active>=0?links[active]:links[0];if(target)location.href=target.getAttribute('href');}else if(input.value.trim()){location.href='/search?q='+encodeURIComponent(input.value.trim());}}
    });
    document.addEventListener('click',function(e){if(!wrap.contains(e.target))close();});
    fetch('/content-index.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error('index unavailable');return r.json();}).then(function(data){posts=Array.isArray(data.posts)?data.posts:[];render();}).catch(function(){posts=[];});
    var form=input.closest('form');if(form)form.addEventListener('submit',function(e){e.preventDefault();var first=results.querySelector('.ed-search-result');if(first)location.href=first.getAttribute('href');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();