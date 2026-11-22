(function(){
  "use strict";
  var groups=["ssc","railway","banking","police","teaching","upsc","rajasthan","other"];
  function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
  function safeUrl(v){try{var u=new URL(String(v||""));return u.protocol==="https:"?u.href:""}catch(_){return ""}}
  function renderPaper(p){
    var paper=safeUrl(p.paperUrl),key=safeUrl(p.answerKeyUrl),source=safeUrl(p.sourceUrl);
    if(!paper)return "";
    var meta=[p.exam,p.year,p.shift].filter(Boolean).map(function(x){return "<span>"+esc(x)+"</span>"}).join("");
    var actions='<a href="'+esc(paper)+'" target="_blank" rel="noopener noreferrer">Question Paper PDF ↗</a>';
    if(key)actions+='<a class="secondary" href="'+esc(key)+'" target="_blank" rel="noopener noreferrer">Answer Key ↗</a>';
    if(source)actions+='<a class="secondary" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">Official Source ↗</a>';
    return '<article class="pyq-paper-card"><h3>'+esc(p.title||p.exam||"Question Paper")+'</h3><div class="pyq-paper-meta">'+meta+'</div>'+(p.description?'<p class="pyq-paper-description">'+esc(p.description)+'</p>':"")+'<div class="pyq-paper-actions">'+actions+'</div></article>';
  }
  fetch("/question-papers/manifest.json",{cache:"no-store"}).then(function(r){if(!r.ok)throw new Error("Paper library unavailable");return r.json()}).then(function(data){
    var papers=Array.isArray(data.papers)?data.papers:[];
    groups.forEach(function(id){
      var host=document.querySelector('[data-paper-category="'+id+'"]');if(!host)return;
      var rows=papers.filter(function(p){return p&&p.category===id&&p.status!=="draft"}).sort(function(a,b){return String(b.year||"").localeCompare(String(a.year||""))||String(b.publishedAt||"").localeCompare(String(a.publishedAt||""))});
      host.innerHTML=rows.length?rows.map(renderPaper).join(""):'<div class="pyq-empty"><b>अभी कोई पेपर उपलब्ध नहीं है</b>इस category में नया paper publish होते ही यहाँ दिखाई देगा।</div>';
    });
  }).catch(function(){
    groups.forEach(function(id){var host=document.querySelector('[data-paper-category="'+id+'"]');if(host)host.innerHTML='<div class="pyq-empty">Question paper library अभी load नहीं हो पाई। कृपया थोड़ी देर बाद refresh करें।</div>'});
  });
})();