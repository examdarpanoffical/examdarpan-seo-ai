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
 const r=await fetch("/question-papers/manifest.json?refresh="+Date.now(),{cache:"no-store"});
 if(!r.ok)throw new Error("Public question paper manifest load नहीं हुई।");
 const j=await r.json();papers=Array.isArray(j.papers)?j.papers:[];renderList();return papers;
}
function shiftsOf(p){
 if(Array.isArray(p.shifts)&&p.shifts.length)return p.shifts;
 if(p.paperUrl)return [{number:1,label:p.shift||"Shift 1",paperUrl:p.paperUrl,answerKeyUrl:p.answerKeyUrl||"",sourceUrl:p.sourceUrl||""}];
 return [];
}
function renderList(){
 const host=$("questionPaperAdminList");
 const rows=papers.filter(p=>p&&p.status!=="draft");
 host.innerHTML=rows.length?rows.map(p=>{
  const shifts=shiftsOf(p);
  return '<div class="card pad" style="margin:8px 0"><strong>'+esc(p.title)+'</strong><div class="meta">'+esc(categories[p.category]||p.category)+' · '+esc(p.exam)+' · '+esc(p.year)+' · '+shifts.length+' Shifts</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px"><button type="button" class="btn btn-dark" data-paper-edit="'+esc(p.id)+'">Edit</button><button type="button" class="btn btn-gold" data-paper-delete="'+esc(p.id)+'">Delete</button>'+shifts.map((x,i)=>'<a href="'+esc(x.paperUrl)+'" target="_blank" rel="noopener">Shift '+(i+1)+' PDF ↗</a>').join(" ")+'</div></div>';
 }).join(""):"अभी कोई paper manifest में publish नहीं हुआ है।";
 host.querySelectorAll("[data-paper-edit]").forEach(b=>b.addEventListener("click",()=>fill(papers.find(p=>p.id===b.dataset.paperEdit))));
 host.querySelectorAll("[data-paper-delete]").forEach(b=>b.addEventListener("click",()=>removePaper(b.dataset.paperDelete)));
}
function renderShiftFields(count,values=[]){
 const host=$("paperShiftFields");
 const old=Array.from(host.querySelectorAll("[data-shift-index]")).map(box=>({
  label:box.querySelector("[data-shift-label]")?.value||"",
  paperUrl:box.querySelector("[data-shift-paper]")?.value||"",
  answerKeyUrl:box.querySelector("[data-shift-key]")?.value||"",
  sourceUrl:box.querySelector("[data-shift-source]")?.value||""
 }));
 const prior=values.length?values:old;
 host.innerHTML="";
 for(let i=0;i<count;i++){
  const v=prior[i]||{};
  const box=document.createElement("section");box.className="card pad";box.style.cssText="grid-column:1/-1;margin:8px 0;border:1px solid #dbe4ef;background:#fff";box.dataset.shiftIndex=String(i+1);
  box.innerHTML='<h3 style="margin:0 0 12px">Shift '+(i+1)+' Paper</h3><div class="admin-form-grid"><div class="field"><label>Shift Name</label><input data-shift-label placeholder="Shift '+(i+1)+'" value="'+esc(v.label||("Shift "+(i+1)))+'"></div><div class="field"><label>Question Paper PDF URL *</label><input data-shift-paper type="url" placeholder="https://.../shift-'+(i+1)+'.pdf" value="'+esc(v.paperUrl||"")+'"></div><div class="field"><label>Answer Key PDF URL</label><input data-shift-key type="url" placeholder="https://.../answer-key-shift-'+(i+1)+'.pdf" value="'+esc(v.answerKeyUrl||"")+'"></div><div class="field"><label>Official Source URL</label><input data-shift-source type="url" placeholder="https://official-site.gov.in/..." value="'+esc(v.sourceUrl||"")+'"></div></div>';
  host.appendChild(box);
 }
}
function collectShifts(){
 return Array.from($("paperShiftFields").querySelectorAll("[data-shift-index]")).map((box,i)=>({
  label:box.querySelector("[data-shift-label]").value.trim()||"Shift "+(i+1),
  paperUrl:box.querySelector("[data-shift-paper]").value.trim(),
  answerKeyUrl:box.querySelector("[data-shift-key]").value.trim(),
  sourceUrl:box.querySelector("[data-shift-source]").value.trim()
 }));
}
function fill(p){
 if(!p)return;
 const shifts=shiftsOf(p);
 $("paperId").value=p.id||"";$("paperTitle").value=p.title||"";$("paperExam").value=p.exam||"";$("paperCategory").value=p.category||"rajasthan";$("paperYear").value=p.year||"";$("paperShiftCount").value=String(Math.max(1,shifts.length));$("paperDescription").value=p.description||"";
 renderShiftFields(Math.max(1,shifts.length),shifts);
 $("publishQuestionPaper").textContent="Update Question Papers";$("questionPaperManager").scrollIntoView({behavior:"smooth",block:"start"});
}
function clearForm(){
 ["paperId","paperTitle","paperExam","paperYear","paperDescription"].forEach(id=>$(id).value="");
 $("paperCategory").value="rajasthan";$("paperShiftCount").value="1";renderShiftFields(1);
 $("publishQuestionPaper").textContent="Publish Question Papers";
}
async function callWorker(payload){
 if(!auth.currentUser||!adminReady)throw new Error("Admin permission verify नहीं हुई।");
 if(!endpoint)throw new Error("Secure Admin Worker URL configured नहीं है।");
 const token=await auth.currentUser.getIdToken();
 const r=await fetch(endpoint,{method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({action:"manage-question-paper",...payload})});
 const body=await r.json().catch(()=>({}));
 if(!r.ok)throw new Error(body.error||"Question paper update failed (HTTP "+r.status+").");
 if(!body.commit)throw new Error("Worker ने GitHub commit SHA return नहीं किया। Save confirm नहीं हुआ; कृपया Worker deployment जाँचें।");
 return body;
}
$("paperShiftCount")?.addEventListener("input",()=>{
 const count=Math.max(1,Math.min(30,Number($("paperShiftCount").value)||1));
 renderShiftFields(count);
});
$("publishQuestionPaper")?.addEventListener("click",async()=>{
 const button=$("publishQuestionPaper");
 try{
  const title=$("paperTitle").value.trim(),exam=$("paperExam").value.trim(),year=String($("paperYear").value||"").trim(),shiftCount=Number($("paperShiftCount").value);
  if(!title||!exam||!/^\d{4}$/.test(year))throw new Error("Title, Exam और valid Year जरूरी हैं।");
  if(!Number.isInteger(shiftCount)||shiftCount<1||shiftCount>30)throw new Error("1 से 30 तक shifts की संख्या चुनें।");
  const shifts=collectShifts();
  if(shifts.length!==shiftCount)throw new Error("सभी shifts के PDF fields बनाएं।");
  shifts.forEach((x,i)=>{
   if(!x.paperUrl)throw new Error("Shift "+(i+1)+" का Question Paper PDF URL जरूरी है।");
   for(const key of ["paperUrl","answerKeyUrl","sourceUrl"])if(x[key]&&new URL(x[key]).protocol!=="https:")throw new Error("Shift "+(i+1)+" के सभी links HTTPS होने चाहिए।");
  });
  const data={id:$("paperId").value||slug([exam,year,title].join("-")),title,exam,category:$("paperCategory").value,year,shiftCount,shifts,description:$("paperDescription").value.trim()};
  button.disabled=true;message("हर shift के links verify करके GitHub में save किया जा रहा है…");
  const result=await callWorker(data);
  const saved=result.item;
  if(!saved||!saved.id)throw new Error("GitHub commit हुआ, लेकिन saved exam record response में नहीं मिला।");
  papers=[saved,...papers.filter(p=>p.id!==saved.id)];renderList();clearForm();
  message("सभी "+shiftCount+" shifts GitHub commit में save हुईं ("+result.commit.slice(0,7)+")। Firebase deploy के बाद student hub पर दिखाई देंगी।");
 }catch(e){message(e.message||String(e),true)}
 finally{button.disabled=false}
});
async function removePaper(id){
 if(!confirm("इस exam के सभी shift papers को Previous Papers Hub से हटाना है?"))return;
 try{const result=await callWorker({operation:"delete",id});papers=papers.filter(p=>p.id!==id);renderList();message("Exam और उसकी सभी shifts delete commit में हटाई गईं ("+result.commit.slice(0,7)+")।")}
 catch(e){message(e.message||String(e),true)}
}
$("clearQuestionPaper")?.addEventListener("click",clearForm);
renderShiftFields(1);
onAuthStateChanged(auth,async user=>{
 adminReady=false;if(!user)return;
 try{const snap=await getDoc(doc(db,"admins",user.uid));if(!snap.exists())throw new Error("Admin authorization failed.");adminReady=true;await readManifest()}
 catch(e){$("paperPublisherMsg").textContent=e.message||"Admin verification failed";$("paperPublisherMsg").style.color="#b91c1c"}
});
