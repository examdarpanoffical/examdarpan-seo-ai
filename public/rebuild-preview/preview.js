/* Exam Darpan rebuild preview — read-only renderer for generated public content index. */
(function(){
  "use strict";
  var groups=[
    {id:"jobs",title:"Latest Government Jobs",cats:["Rajasthan Jobs","Government Jobs","Police & Defence Jobs","Teaching Jobs","Railway Jobs","Banking Jobs","SSC Jobs","UPSC Jobs"],url:"/all-india-government-jobs"},
    {id:"results",title:"Latest Results",cats:["Results"],url:"/category-results"},
    {id:"admit",title:"Admit Card",cats:["Admit Card"],url:"/category-admit-card"},
    {id:"answer",title:"Answer Key",cats:["Answer Key"],url:"/category-answer-key"},
    {id:"admission",title:"Admissions & Scholarships",cats:["Scholarships","University & College","Entrance Exams"],url:"/category-scholarships"},
    {id:"syllabus",title:"Syllabus & Exam Updates",cats:["Syllabus","Latest Updates","Yojana"],url:"/category-syllabus"}
  ];
  var categoryAliases={"Rajasthan":"Rajasthan Jobs","All India Jobs":"Government Jobs","Admit Cards":"Admit Card","Result":"Results","Answer Keys":"Answer Key","Exam Syllabus":"Syllabus"};
  function normalizedCategory(p){var raw=String(p.category||p.categoryName||"").trim();return categoryAliases[raw]||(["Rajasthan Jobs","Government Jobs","Police & Defence Jobs","Teaching Jobs","Railway Jobs","Banking Jobs","SSC Jobs","UPSC Jobs","Admit Card","Results","Answer Key","Syllabus","Entrance Exams","Scholarships","University & College","Yojana","Latest Updates"].indexOf(raw)>=0?raw:"Latest Updates");}
  var categoryPaths={
    "Rajasthan Jobs":"/rajasthan-government-jobs",
    "Government Jobs":"/all-india-government-jobs",
    "Police & Defence Jobs":"/category-police-defence-jobs",
    "Teaching Jobs":"/category-teaching-jobs",
    "Railway Jobs":"/category-railway-jobs",
    "Banking Jobs":"/category-banking-jobs",
    "SSC Jobs":"/category-ssc-jobs",
    "UPSC Jobs":"/category-upsc-jobs",
    "Admit Card":"/category-admit-card","Results":"/category-results",
    "Answer Key":"/category-answer-key","Syllabus":"/category-syllabus",
    "Entrance Exams":"/category-entrance-exams","Scholarships":"/category-scholarships",
    "University & College":"/category-university-college","Yojana":"/category-yojana",
    "Latest Updates":"/category-latest-updates"
  };
  var esc=function(v){return String(v==null?"":v).replace(/[&<>'"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c];});};
  var date=function(v){if(!v)return "";var d=new Date(v);return isNaN(d)?"":new Intl.DateTimeFormat("en-IN",{day:"2-digit",month:"short",year:"numeric"}).format(d);};
  var slugUrl=function(p){var s=String(p.slug||p.urlSlug||p.seoSlug||"").replace(/^\/+|\.html$/g,"");return s?"/"+encodeURIComponent(s):"#";};
  var categoryPath=function(c){var m={"Rajasthan Jobs":"rajasthan-government-jobs","Government Jobs":"all-india-government-jobs","Admit Card":"category-admit-card","Results":"category-results","Answer Key":"category-answer-key","Syllabus":"category-syllabus","Scholarships":"category-scholarships","University & College":"category-university-college","Entrance Exams":"category-entrance-exams","Yojana":"category-yojana","Latest Updates":"category-latest-updates","Police & Defence Jobs":"category-police-defence-jobs","Teaching Jobs":"category-teaching-jobs","Railway Jobs":"category-railway-jobs","Banking Jobs":"category-banking-jobs","SSC Jobs":"category-ssc-jobs","UPSC Jobs":"category-upsc-jobs"};return "/"+(m[c]||"category-latest-updates");};
  var status=function(p){return String(p.applicationStatus||p.jobStatus||p.statusLabel||"").trim();};
  function postCard(p){
    var href=slugUrl(p),cat=p.category||p.categoryName||"Latest Updates";
    return '<a href="'+esc(href)+'"><b class="dot blue"></b><span>'+esc(p.title||p.seoTitle||"Latest update")+'</span>'+(status(p)?'<small>'+esc(status(p).toUpperCase())+'</small>':'')+'</a>';
  }
  function render(posts){
    groups.forEach(function(g){
      var panel=document.getElementById(g.id);if(!panel)return;
      var arr=posts.filter(function(p){return g.cats.indexOf(normalizedCategory(p))!==-1;}).slice(0,6);
      var body=panel.querySelector(".list-body");
      var foot=panel.querySelector("footer a");
      var head=panel.querySelector("header h2");
      if(head)head.textContent=g.title;
      if(body)body.innerHTML=arr.length?arr.map(postCard).join(""):'<div class="empty-state">इस category में अभी कोई published update उपलब्ध नहीं है।</div>';
      if(foot){foot.href=g.url;foot.textContent="सभी अपडेट देखें →";}
      var headLink=panel.querySelector("header>a");if(headLink)headLink.href=g.url;
    });
    var total=document.getElementById("published-count");
    if(total)total.textContent=posts.length+" Published Updates";
    var latest=document.getElementById("latest-updates");
    if(latest)latest.innerHTML=posts.slice(0,8).map(postCard).join("");
  }
  function setupSearch(posts){
    var input=document.getElementById("portal-search"),box=document.getElementById("search-results");
    if(!input||!box)return;
    function update(){
      var q=input.value.trim().toLocaleLowerCase();
      if(q.length<2){box.hidden=true;box.innerHTML="";return;}
      var matches=posts.filter(function(p){return [p.title,p.category,p.excerpt,p.description].concat(p.tags||[]).join(" ").toLocaleLowerCase().includes(q);}).slice(0,8);
      box.innerHTML=matches.length?matches.map(function(p){return '<a href="'+esc(slugUrl(p))+'"><strong>'+esc(p.title||"Latest update")+'</strong><small>'+esc(normalizedCategory(p))+'</small></a>';}).join(""):'<p>इस keyword से कोई published update नहीं मिली।</p>';
      box.hidden=false;
    }
    input.addEventListener("input",update);
    input.addEventListener("focus",update);
    document.addEventListener("click",function(e){if(!box.contains(e.target)&&e.target!==input)box.hidden=true;});
    input.addEventListener("keydown",function(e){if(e.key==="Escape")box.hidden=true;if(e.key==="Enter"){var first=box.querySelector("a");if(first){e.preventDefault();location.href=first.href;}}});
  }
  fetch("/content-index.json",{cache:"no-cache"}).then(function(r){if(!r.ok)throw new Error("content index unavailable: "+r.status);return r.json();}).then(function(data){
    var posts=Array.isArray(data.posts)?data.posts:[];
    posts=posts.filter(function(p){return p&&p.slug;}).sort(function(a,b){return new Date(b.publishedAt||0)-new Date(a.publishedAt||0);});
    render(posts);setupSearch(posts);
    var status=document.getElementById("feed-status");
    if(status)status.textContent=posts.length?"Live published content connected":"No published posts in content index";
  }).catch(function(err){
    console.warn("Exam Darpan preview content feed:",err);
    var status=document.getElementById("feed-status");
    if(status)status.textContent="Published content feed unavailable — generator output required";
    groups.forEach(function(g){var b=document.querySelector("#"+g.id+" .list-body");if(b)b.innerHTML='<div class="empty-state">Published updates load after the static content index is generated.</div>';});
  });
})();