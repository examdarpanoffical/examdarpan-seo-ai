(function(){
  if (document.getElementById("ed-side-menu")) return;
  var host=document.querySelector(".site-head .head-row")||document.querySelector(".top .container");
  if(!host) return;
  var trigger=document.createElement("button");
  trigger.type="button";trigger.className="ed-menu-trigger";trigger.setAttribute("aria-expanded","false");trigger.setAttribute("aria-controls","ed-side-menu");
  trigger.innerHTML='<span class="ed-menu-lines" aria-hidden="true"><i></i><i></i><i></i></span><span>Menu</span>';
  trigger.setAttribute("aria-label","Open categories menu");
  host.appendChild(trigger);
  var overlay=document.createElement("button");overlay.type="button";overlay.className="ed-menu-overlay";overlay.setAttribute("aria-label","Close menu");
  var panel=document.createElement("aside");panel.id="ed-side-menu";panel.className="ed-side-menu";panel.setAttribute("aria-label","Exam Darpan navigation");
  panel.innerHTML='<div class="ed-side-head"><div><b>EXAM <em>DARPAN</em></b><small>Explore categories & student tools</small></div><button type="button" class="ed-menu-close" aria-label="Close menu">×</button></div>'+
  '<div class="ed-side-content">'+
  '<section><h2>मुख्य श्रेणियाँ</h2><a href="/rebuild-preview/categories.html">सभी Categories <span>›</span></a><a href="/rebuild-preview/category.html?category=Rajasthan%20Jobs">Rajasthan Government Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=Government%20Jobs">All India Government Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=SSC%20Jobs">SSC Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=UPSC%20Jobs">UPSC Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=Railway%20Jobs">Railway Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=Banking%20Jobs">Banking Jobs <span>›</span></a><a href="/rebuild-preview/category.html?category=Police%20%26%20Defence%20Jobs">Police & Defence <span>›</span></a><a href="/rebuild-preview/category.html?category=Teaching%20Jobs">Teaching Jobs <span>›</span></a></section>'+
  '<section><h2>परीक्षा अपडेट</h2><a href="/rebuild-preview/category.html?category=Results">Latest Results <span>›</span></a><a href="/rebuild-preview/category.html?category=Admit%20Card">Admit Card & Exam City <span>›</span></a><a href="/rebuild-preview/category.html?category=Answer%20Key">Answer Key <span>›</span></a><a href="/rebuild-preview/category.html?category=Scholarships">Admission & Scholarships <span>›</span></a><a href="/rebuild-preview/category.html?category=Syllabus">Syllabus & Exam Pattern <span>›</span></a><a href="/rebuild-preview/category.html?category=Entrance%20Exams">Entrance Exams <span>›</span></a></section>'+
  '<section><h2>Student Corner</h2><a href="/rebuild-preview/job-search.html">Smart Job Search <span>↗</span></a><a href="/rebuild-preview/saved-jobs.html">Saved Jobs <span>↗</span></a><a href="/rebuild-preview/previous-papers.html">Previous Year Papers <span>↗</span></a><a href="/mock-tests/">Mock Tests & Practice <span>↗</span></a><a href="/quiz">Daily Quiz <span>↗</span></a></section>'+
  '</div><div class="ed-side-foot"><a href="/rebuild-preview/index.html">Exam Darpan Home</a><span>Rajasthan + All India</span></div>';
  document.body.appendChild(overlay);document.body.appendChild(panel);
  function open(){document.body.classList.add("ed-menu-open");trigger.setAttribute("aria-expanded","true");trigger.setAttribute("aria-label","Close categories menu");panel.querySelector(".ed-menu-close").focus();}
  function close(){document.body.classList.remove("ed-menu-open");trigger.setAttribute("aria-expanded","false");trigger.setAttribute("aria-label","Open categories menu");trigger.focus();}
  trigger.addEventListener("click",function(){document.body.classList.contains("ed-menu-open")?close():open();});
  overlay.addEventListener("click",close);panel.querySelector(".ed-menu-close").addEventListener("click",close);
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&document.body.classList.contains("ed-menu-open"))close();});
})();