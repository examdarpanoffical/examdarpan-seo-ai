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
  '<section><h2>मुख्य श्रेणियाँ</h2><a href="/categories.html">सभी Categories <span>›</span></a><a href="/rajasthan-government-jobs">Rajasthan Government Jobs <span>›</span></a><a href="/all-india-government-jobs">All India Government Jobs <span>›</span></a><a href="/category-ssc-jobs">SSC Jobs <span>›</span></a><a href="/category-upsc-jobs">UPSC Jobs <span>›</span></a><a href="/category-railway-jobs">Railway Jobs <span>›</span></a><a href="/category-banking-jobs">Banking Jobs <span>›</span></a><a href="/category-police-defence-jobs">Police & Defence <span>›</span></a><a href="/category-teaching-jobs">Teaching Jobs <span>›</span></a></section>'+
  '<section><h2>परीक्षा अपडेट</h2><a href="/category-results">Latest Results <span>›</span></a><a href="/category-admit-card">Admit Card & Exam City <span>›</span></a><a href="/category-answer-key">Answer Key <span>›</span></a><a href="/category-scholarships">Admission & Scholarships <span>›</span></a><a href="/category-syllabus">Syllabus & Exam Pattern <span>›</span></a><a href="/category-entrance-exams">Entrance Exams <span>›</span></a><a href="/category-university-college">University & College <span>›</span></a><a href="/category-yojana">Yojana <span>›</span></a><a href="/category-latest-updates">Latest Updates <span>›</span></a></section>'+
  '<section><h2>Student Corner</h2><a href="/job-search.html">Smart Job Search <span>↗</span></a><a href="/saved-jobs.html">Saved Jobs <span>↗</span></a><a href="/previous-papers">Previous Year Papers <span>↗</span></a><a href="/previous-papers#ssc">SSC Previous Papers <span>›</span></a><a href="/previous-papers#railway">Railway Previous Papers <span>›</span></a><a href="/previous-papers#banking">Banking Previous Papers <span>›</span></a><a href="/previous-papers#police">Police & Defence Papers <span>›</span></a><a href="/previous-papers#teaching">Teaching Exam Papers <span>›</span></a><a href="/previous-papers#upsc">UPSC & State PSC Papers <span>›</span></a><a href="/previous-papers#rajasthan">Rajasthan Previous Papers <span>›</span></a><a href="/previous-papers#other">Other State & Central Papers <span>›</span></a><a href="/mock-tests/">Mock Tests & Practice <span>↗</span></a><a href="/quiz">Daily Quiz <span>↗</span></a></section>'+
  '</div><div class="ed-side-foot"><a href="/">Exam Darpan Home</a><span>Rajasthan + All India</span></div>';
  document.body.appendChild(overlay);document.body.appendChild(panel);
  function open(){document.body.classList.add("ed-menu-open");trigger.setAttribute("aria-expanded","true");trigger.setAttribute("aria-label","Close categories menu");panel.querySelector(".ed-menu-close").focus();}
  function close(){document.body.classList.remove("ed-menu-open");trigger.setAttribute("aria-expanded","false");trigger.setAttribute("aria-label","Open categories menu");trigger.focus();}
  trigger.addEventListener("click",function(){document.body.classList.contains("ed-menu-open")?close():open();});
  overlay.addEventListener("click",close);panel.querySelector(".ed-menu-close").addEventListener("click",close);
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&document.body.classList.contains("ed-menu-open"))close();});
})();