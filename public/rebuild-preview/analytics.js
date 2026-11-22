/* Exam Darpan preview analytics. Uses the site's existing GA4 measurement ID. */
(function(){
"use strict";
var ID="G-FWB3YMTSDX";
window.dataLayer=window.dataLayer||[];
window.gtag=window.gtag||function(){window.dataLayer.push(arguments)};
window.gtag("js",new Date());
window.gtag("config",ID,{send_page_view:true});
var loaded=false;
function load(){
 if(loaded)return;loaded=true;
 var s=document.createElement("script");s.async=true;
 s.src="https://www.googletagmanager.com/gtag/js?id="+ID;
 document.head.appendChild(s);
}
if("requestIdleCallback" in window)requestIdleCallback(load,{timeout:2500});else setTimeout(load,1800);
function track(name,label,callback){
 load();
 window.gtag("event",name,{event_category:"exam_darpan_portal",event_label:label||"not_set",event_callback:callback||function(){},event_timeout:900});
}
document.addEventListener("click",function(e){
 var a=e.target.closest("a[data-analytics-event]");
 if(!a)return;
 var name=a.getAttribute("data-analytics-event");
 var label=a.getAttribute("data-analytics-label")||a.getAttribute("href")||"";
 if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target==="_blank") {
   track(name,label);return;
 }
 e.preventDefault();
 var done=false;
 function go(){if(done)return;done=true;window.location.assign(a.href);}
 track(name,label,go);
 setTimeout(go,1100);
});
document.addEventListener("submit",function(e){
 if(e.target.matches(".search"))track("portal_search_submit","search_box");
},true);
document.addEventListener("click",function(e){
 var a=e.target.closest("#search-results a");
 if(a)track("portal_search_result_click","search_suggestion");
},true);
})();
