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
function track(name,label){
 window.gtag("event",name,{event_category:"exam_darpan_portal",event_label:label||"not_set"});
}
document.addEventListener("click",function(e){
 var a=e.target.closest("a[data-analytics-event]");
 if(!a)return;
 var name=a.getAttribute("data-analytics-event");
 var label=a.getAttribute("data-analytics-label")||a.getAttribute("href")||"";
 track(name,label);
});
document.addEventListener("submit",function(e){
 if(e.target.matches(".search"))track("portal_search_submit","search_box");
},true);
document.addEventListener("click",function(e){
 if(e.target.closest("#search-results a"))track("portal_search_result_click","search_suggestion");
},true);
})();
