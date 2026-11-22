import{initializeApp,getApps,getApp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js';
import{getAuth,onAuthStateChanged}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js';
import{getFirestore,doc,getDoc}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js';
const $=id=>document.getElementById(id);
const app=getApps().length?getApp():initializeApp(window.FIREBASE_CONFIG);
const auth=getAuth(app),db=getFirestore(app);
const endpoint=String(window.EXAMDARPAN_PUBLISH_TRIGGER_URL||'').trim();
let adminReady=false,papers=[];
const categories={ssc:"SSC Exams",railway:"Railway Exams",banking:"Banking Exams",police:"Police & Defence",teaching:"Teaching Exams",upsc:"UPSC & State PSC",rajasthan:"Rajasthan Exams",other:"Other State & Central Exams"};
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function slug(v){return String(v||"").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,90)}
function message(t,error=false){$("paperPublisherMsg").textContent=t;$("paperPublisherMsg").style.color=error?"#b91c1c":"#166534"}
async function readManifest(){
 try{const r=await fetch("/question-papers/manifest.json",{cache:"no-store"});if(!r.ok)throw new Error("Library not deployed yet");const j=await r.json();papers=Array.isArray(j.papers)?j.papers:[];renderList()}
 catch(e){$("questionPaperAdminList").textContent="Manifest अभी deploy नहीं हुई है। पहली बार deploy होने के बाद list यहाँ दिखेगी।"}
}
function renderList(){
 const host=$("questionPaperAdminList");
 const rows=papers.filter(p=>p&&p.status!=="draft");
 host.innerHTML=rows.length?rows.map(p=>'<div class="card pad" style="margin:8px 0"><strong>'+esc(p.title)+'</strong><div class="meta">'+esc(categories[p.category]||p.category)+' · '+esc(p.exam)+' · '+esc(p.year)+' · '+esc(p.shift||"")+'</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px"><button type="button" class="btn btn-dark" data-paper-edit="'+esc(p.id)+'">Edit</button><button type="button" class="btn btn-gold" data-paper-delete="'+esc(p.id)+'">Delete</button><a href="'+esc(p.paperUrl)+'" target="_blank" rel="noopener">PDF ↗</a></div></div>').join(""):"अभी कोई paper publish नहीं हुआ है।";
 host.querySelectorAll("[data-paper-edit]").forEach(b=>b.addEventListener("click",()=>fill(papers.find(p=>p.id===b.dataset.paperEdit))));
 host.querySelectorAll("[data-paper-delete]").forEach(b=>b.addEventListener("click",()=>removePaper(b.dataset.paperDelete)));
}
function fill(p){
 if(!p)return;
 $("paperId").value=p.id||"";$("paperTitle").value=p.title||"";$("paperExam").value=p.exam||"";$("paperCategory").value=p.category||"rajasthan";$("paperYear").value=p.year||"";$("paperShift").value=p.shift||"";$("paperUrl").value=p.paperUrl||"";$("paperAnswerKeyUrl").value=p.answerKeyUrl||"";$("paperSourceUrl").value=p.sourceUrl||"";$("paperDescription").value=p.description||"";
 $("publishQuestionPaper").textContent="Update Question Paper";$("questionPaperManager").scrollIntoView({behavior:"smooth",block:"start"});
}
function clearForm(){
 ["paperId","paperTitle","paperExam","paperYear","paperShift","paperUrl","paperAnswerKeyUrl","paperSourceUrl","paperDescription"].forEach(id=>$(id).value="");
 $("paperCategory").value="rajasthan";$("publishQuestionPaper").textContent="Publish Question Paper";
}
async function callWorker(payload){
 if(!auth.currentUser||!adminReady)throw new Error("Admin permission verify नहीं हुई।");
 if(!endpoint)throw new Error("Secure Admin Worker URL configured नहीं है।");
 const token=await auth.currentUser.getIdToken();
 const r=await fetch(endpoint,{method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({action:"manage-question-paper",...payload})});
 const body=await r.json().catch(()=>({}));
 if(!r.ok)throw new Error(body.error||"Question paper update failed (HTTP "+r.status+").");
 return body;
}
$("publishQuestionPaper")?.addEventListener("click",async()=>{
 const button=$("publishQuestionPaper");
 try{
  const title=$("paperTitle").value.trim(),exam=$("paperExam").value.trim(),year=String($("paperYear").value||"").trim(),paperUrl=$("paperUrl").value.trim();
  if(!title||!exam||!/^\d{4}$/.test(year)||!paperUrl)throw new Error("Title, Exam, Year और Question Paper PDF URL जरूरी हैं।");
  const parsed=new URL(paperUrl);if(parsed.protocol!=="https:")throw new Error("PDF URL HTTPS होना चाहिए।");
  const data={id:$("paperId").value||slug([exam,year,$("paperShift").value,title].filter(Boolean).join("-")),title,exam,category:$("paperCategory").value,year,shift:$("paperShift").value.trim(),paperUrl,answerKeyUrl:$("paperAnswerKeyUrl").value.trim(),sourceUrl:$("paperSourceUrl").value.trim(),description:$("paperDescription").value.trim()};
  for(const key of ["answerKeyUrl","sourceUrl"])if(data[key]&&new URL(data[key]).protocol!=="https:")throw new Error("सभी PDF और source links HTTPS होने चाहिए।");
  button.disabled=true;message("Secure publisher से save किया जा रहा है…");
  const result=await callWorker(data);
  const saved={...data,id:result.id,status:"published",publishedAt:new Date().toISOString()};
  papers=[saved,...papers.filter(p=>p.id!==saved.id)];renderList();clearForm();
  message("Question paper GitHub library में publish commit हो गया। Hosting deploy पूरा होने के बाद student hub पर दिखाई देगा।");
 }catch(e){message(e.message||String(e),true)}
 finally{button.disabled=false}
});
async function removePaper(id){
 if(!confirm("इस question paper को Previous Papers Hub से हटाना है?"))return;
 try{const result=await callWorker({operation:"delete",id});papers=papers.filter(p=>p.id!==id);renderList();message("Question paper हटाने का commit हो गया। Hosting deploy के बाद hub से हट जाएगा।")}
 catch(e){message(e.message||String(e),true)}
}
$("clearQuestionPaper")?.addEventListener("click",clearForm);
onAuthStateChanged(auth,async user=>{
 adminReady=false;if(!user)return;
 try{const snap=await getDoc(doc(db,"admins",user.uid));if(!snap.exists())throw new Error("Admin authorization failed.");adminReady=true;await readManifest()}
 catch(e){$("paperPublisherMsg").textContent=e.message||"Admin verification failed";$("paperPublisherMsg").style.color="#b91c1c"}
});
