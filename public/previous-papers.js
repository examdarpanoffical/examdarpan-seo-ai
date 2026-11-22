(function(){
  "use strict";
  var groups=["ssc","railway","banking","police","teaching","upsc","rajasthan","other"];
  function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
  function safeUrl(v){try{var u=new URL(String(v||""));return u.protocol==="https:"?u.href:""}catch(_){return ""}}
  function shiftsOf(p){
    if(Array.isArray(p.shifts)&&p.shifts.length)return p.shifts;
    if(p.paperUrl)return [{number:1,label:p.shift||"Shift 1",paper1Url:p.paperUrl,paper2Url:""}];
    return [];
  }
  function renderPaper(p){
    var shifts=shiftsOf(p);
    if(!shifts.length)return "";
    var rows=shifts.map(function(s,i){
      var first=safeUrl(s.paper1Url||s.paperUrl),second=safeUrl(s.paper2Url);
      if(!first&&!second)return "";
      var label=s.label||("Shift "+(i+1));
      var actions="";
      if(first)actions+='<a href="'+esc(first)+'" target="_blank" rel="noopener noreferrer">Paper 1 PDF ↗</a>';
      if(second)actions+='<a class="secondary" href="'+esc(second)+'" target="_blank" rel="noopener noreferrer">Paper 2 PDF ↗</a>';
      return '<div class="pyq-shift-row"><div class="pyq-shift-label">'+esc(label)+'</div><div class="pyq-paper-actions">'+actions+'</div></div>';
    }).join("");
    if(!rows)return "";
    var meta=[p.exam,p.year,(p.paperCount||shifts.length*2)+" Papers"].filter(Boolean).map(function(x){return "<span>"+esc(x)+"</span>"}).join("");
    return '<article class="pyq-paper-card"><h3>'+esc(p.title||p.exam||"Question Paper")+'</h3><div class="pyq-paper-meta">'+meta+'</div>'+(p.description?'<p class="pyq-paper-description">'+esc(p.description)+'</p>':"")+'<div class="pyq-shifts-list">'+rows+'</div></article>';
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