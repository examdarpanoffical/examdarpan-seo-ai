import{initializeApp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js';
import{getAuth,onAuthStateChanged,signOut}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js';
import{getFirestore,doc,getDoc,collection,query,where,orderBy,limit,getDocs,addDoc,updateDoc,deleteDoc,serverTimestamp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js';
import{getAI,getGenerativeModel,GoogleAIBackend}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-ai.js';
import{initializeAppCheck,ReCaptchaEnterpriseProvider}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-app-check.js';

const app=initializeApp(window.FIREBASE_CONFIG);
if(window.FIREBASE_APPCHECK_SITE_KEY){
  try{initializeAppCheck(app,{provider:new ReCaptchaEnterpriseProvider(window.FIREBASE_APPCHECK_SITE_KEY),isTokenAutoRefreshEnabled:true});}
  catch(e){console.warn('App Check initialization failed',e)}
}
const auth=getAuth(app),db=getFirestore(app);
const ai=getAI(app,{backend:new GoogleAIBackend()});
const model=getGenerativeModel(ai,{model:'gemini-3.6-flash'});

let uid=null,all=[];
const $=id=>document.getElementById(id);
const translit=s=>String(s||'').toLowerCase().replace(/[àáâãäå]/g,'a').replace(/[æ]/g,'ae').replace(/[ç]/g,'c').replace(/[èéêë]/g,'e').replace(/[ìíîï]/g,'i').replace(/[ñ]/g,'n').replace(/[òóôõö]/g,'o').replace(/[ùúûü]/g,'u').replace(/[ýÿ]/g,'y');
const slugify=s=>translit(s).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,110);
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cleanContent=s=>DOMPurify.sanitize(String(s||''),{USE_PROFILES:{html:true}});

async function ensureAdmin(user){
  try{
    const snap=await getDoc(doc(db,'admins',user.uid));
    if(!snap.exists())throw new Error('This account is not authorized as admin.');
    uid=user.uid;
    $('authStatus').textContent='Admin verified';
    await loadPosts();
    await loadQuizzes();
    await loadQuizAnalytics();
  }catch(e){
    console.error(e);
    $('authStatus').textContent='Admin verification failed';
    alert(e.message||'Admin verification failed');
    await signOut(auth);
  }
}
onAuthStateChanged(auth,u=>{
  if(!u){location.href='login.html';return}
  ensureAdmin(u);
});

async function loadPosts(){
  $('posts').innerHTML='<div class="empty">Loading posts…</div>';
  try{
    const q=query(collection(db,'posts'),orderBy('updatedAt','desc'));
    const snap=await getDocs(q);
    all=snap.docs.map(d=>({id:d.id,...d.data()}));
    renderList();
  }catch(e){
    console.error(e);
    $('posts').innerHTML='<div class="empty"><strong>Posts load नहीं हुए.</strong><br>'+escapeHtml(e.message||'Firestore error')+'</div>';
  }
}
function renderList(){
  const term=($('filter').value||'').toLowerCase().trim();
  const list=all.filter(p=>(p.title||'').toLowerCase().includes(term)||(p.category||'').toLowerCase().includes(term));
  $('posts').innerHTML=list.map(p=>`<div class="card pad" style="margin-bottom:10px"><strong>${escapeHtml(p.title||'Untitled')}</strong><div class="meta">${escapeHtml(p.category||'')} · ${escapeHtml(p.status||'')} · ${p.publishedAt?'Published':'Draft'}${p.telegramSentAt?' · Telegram sent':(p.status==='published'?' · Telegram pending':'')}</div><div style="margin-top:8px"><button class="btn btn-dark" data-edit="${p.id}">Edit</button> <button class="btn btn-gold" data-delete="${p.id}">Delete</button></div></div>`).join('')||'<div class="empty">No posts found.</div>';
  document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>fill(all.find(p=>p.id===b.dataset.edit)));
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>remove(b.dataset.delete));
}
function fill(p){
  if(!p)return;
  $('postId').value=p.id;$('title').value=p.title||'';$('slug').value=p.slug||'';
  $('category').value=p.category||'Rajasthan Jobs';$('excerpt').value=p.excerpt||'';$('content').value=p.content||'';
  $('image').value=p.featuredImage||'';$('notification').value=p.officialNotificationUrl||'';$('apply').value=p.applyOnlineUrl||'';
  $('official').value=p.officialWebsiteUrl||'';$('pdf').value=p.notificationPdfUrl||'';$('tags').value=(p.tags||[]).join(', ');
  $('formTitle').textContent='Edit Article';window.scrollTo({top:0,behavior:'smooth'});
}
function articleData(status){
  const title=$('title').value.trim();
  const category=$('category').value||'Latest Updates';
  const lower=title.toLowerCase();
  const guards={
    'Admit Card':['admit card','admitcard','hall ticket','प्रवेश पत्र','प्रवेश-पत्र','city intimation','exam city'],
    'Results':['result','परिणाम','scorecard','score card'],
    'Answer Key':['answer key','answerkey','उत्तर कुंजी'],
    'Syllabus':['syllabus','पाठ्यक्रम']
  };
  if(status==='published' && guards[category] && title && !guards[category].some(x=>lower.includes(x))){
    throw new Error(`Category "${category}" title से match नहीं कर रही। सही category चुनें ताकि गलत section में article न जाए.`);
  }
  const content=cleanContent($('content').value);
  const plain=content.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
  const excerpt=$('excerpt').value.trim()||plain.replace(/^AI-assisted draft — Human verification required before publication\.?/i,'').slice(0,155).trim();
  const base={
    title,slug:($('slug').value.trim()||slugify(title)),category:$('category').value||'Latest Updates',
    excerpt,content,featuredImage:$('image').value.trim(),
    officialNotificationUrl:$('notification').value.trim(),applyOnlineUrl:$('apply').value.trim(),
    officialWebsiteUrl:$('official').value.trim(),notificationPdfUrl:$('pdf').value.trim(),
    tags:$('tags').value.split(',').map(x=>x.trim()).filter(Boolean),
    status,updatedAt:serverTimestamp()
  };
  if(status==='published')base.publishedAt=serverTimestamp();
  return base;
}
async function save(status){
  if(!$('title').value.trim()){alert('Title required');return}
  if(!$('content').value.trim()){alert('Article content required');return}
  try{
    const id=$('postId').value,d=articleData(status);
    if(id)await updateDoc(doc(db,'posts',id),d);
    else await addDoc(collection(db,'posts'),{...d,createdAt:serverTimestamp()});
    $('msg').textContent=status==='published'?'Published successfully. Telegram auto-share is queued.':'Draft saved successfully.';
    clearForm();await loadPosts();
  }catch(e){console.error(e);$('msg').textContent='Save error: '+(e.message||e)}
}
async function remove(id){
  if(!confirm('Delete this post?'))return;
  try{await deleteDoc(doc(db,'posts',id));await loadPosts()}catch(e){alert(e.message||'Delete failed')}
}
function clearForm(){
  $('postId').value='';
  ['title','slug','excerpt','content','image','notification','apply','official','pdf','tags','aiTopic','aiSource'].forEach(id=>{if($(id))$(id).value=''});
  $('formTitle').textContent='New Article';
  $('aiMsg').textContent='';$('aiImageMsg').textContent='';
  $('aiImagePreview').innerHTML='';
}
$('saveDraft').onclick=()=>save('draft');
$('publish').onclick=()=>save('published');
$('clear').onclick=clearForm;
$('filter').oninput=renderList;
$('logout').onclick=()=>signOut(auth);


/* ---------------- Daily Quiz CMS ---------------- */
let quizQuestions=[];
function todayISO(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
function newQuizQuestion(q={}){quizQuestions.push({question:q.question||'',options:Array.isArray(q.options)&&q.options.length===4?q.options:['','','',''],answerIndex:Number.isInteger(q.answerIndex)?q.answerIndex:0,explanation:q.explanation||''});renderQuizEditor();}
function renderQuizEditor(){
  const box=$('quizQuestions');if(!box)return;
  box.innerHTML=quizQuestions.map((q,i)=>`<div class="quiz-admin-question card pad"><div class="quiz-admin-qhead"><strong>Question ${i+1}</strong><button type="button" class="btn btn-light" data-qremove="${i}">Remove</button></div>
  <div class="field"><label>Question</label><textarea data-qfield="${i}:question" rows="3" placeholder="Question text">${escapeHtml(q.question)}</textarea></div>
  <div class="quiz-admin-options">${q.options.map((o,j)=>`<div class="field"><label>Option ${String.fromCharCode(65+j)}</label><input data-qfield="${i}:option:${j}" value="${escapeHtml(o)}"></div>`).join('')}</div>
  <div class="admin-form-grid"><div class="field"><label>Correct Answer</label><select data-qfield="${i}:answer">${q.options.map((o,j)=>`<option value="${j}" ${q.answerIndex===j?'selected':''}>${String.fromCharCode(65+j)}${o?` — ${escapeHtml(o).slice(0,55)}`:''}</option>`).join('')}</select></div>
  <div class="field"><label>Explanation</label><textarea data-qfield="${i}:explanation" rows="2" placeholder="क्यों सही है?">${escapeHtml(q.explanation)}</textarea></div></div></div>`).join('')||'<div class="empty">पहला question add करें।</div>';
  box.querySelectorAll('[data-qremove]').forEach(b=>b.onclick=()=>{quizQuestions.splice(Number(b.dataset.qremove),1);renderQuizEditor()});
  box.querySelectorAll('[data-qfield]').forEach(el=>el.oninput=()=>syncQuizField(el));
}
function syncQuizField(el){
  const parts=el.dataset.qfield.split(':'),i=Number(parts[0]),type=parts[1],idx=Number(parts[2]);
  if(!quizQuestions[i])return;
  if(type==='question')quizQuestions[i].question=el.value;
  if(type==='option')quizQuestions[i].options[idx]=el.value;
  if(type==='answer')quizQuestions[i].answerIndex=Number(el.value);
  if(type==='explanation')quizQuestions[i].explanation=el.value;
}
function clearQuizForm(){
  $('quizId').value='';$('quizDate').value=todayISO();$('quizDuration').value=10;$('quizTitle').value='';$('quizDescription').value='';
  quizQuestions=[];renderQuizEditor();$('quizMsg').textContent='';
}
function quizData(status){
  const clean=quizQuestions.map(q=>({question:q.question.trim(),options:q.options.map(x=>x.trim()),answerIndex:Number(q.answerIndex),explanation:q.explanation.trim()}));
  if(!clean.length)throw new Error('कम से कम 1 question add करें.');
  if(clean.some(q=>!q.question||q.options.some(x=>!x)||q.options.length!==4))throw new Error('हर question में question text और चारों options भरें.');
  if(clean.some(q=>q.answerIndex<0||q.answerIndex>3))throw new Error('हर question का correct answer select करें.');
  const date=$('quizDate').value;if(!date)throw new Error('Quiz date required.');
  const ratio=$('quizNegativeRatio')?.value||'1/3';
  let negativeNumerator=1,negativeDenominator=3;
  if(ratio==='custom'){
    negativeNumerator=Math.max(1,Number($('quizNegativeNumerator')?.value)||1);
    negativeDenominator=Math.max(1,Number($('quizNegativeDenominator')?.value)||3);
  }else{
    const parts=ratio.split('/');
    negativeNumerator=Number(parts[0])||1;
    negativeDenominator=Number(parts[1])||3;
  }

  return {
    title:$('quizTitle').value.trim()||`Daily Quiz — ${date}`,
    description:$('quizDescription').value.trim(),
    quizDate:date,
    durationMinutes:Math.min(300,Math.max(1,Number($('quizDuration').value)||10)),
    testType:$('quizTestType')?.value||'daily',
    marksPerQuestion:Math.max(0.01,Number($('quizMarks')?.value)||1),
    negativeMarkingEnabled:($('quizNegativeEnabled')?.value||'on')==='on',
    negativeNumerator,
    negativeDenominator,
    leaderboardEnabled:($('quizLeaderboard')?.value||'on')==='on',
    showRankAfterSubmit:($('quizShowRank')?.value||'on')==='on',
    questions:clean,
    status,
    updatedAt:serverTimestamp()
  };
}
async function saveQuiz(status){
  try{
    const data=quizData(status),id=$('quizId').value;
    if(status==='published'){
      const existing=await getDocs(query(collection(db,'quizzes'),where('status','==','published'),where('quizDate','==',data.quizDate),limit(3)));
      const clash=existing.docs.find(s=>s.id!==id);
      if(clash)throw new Error('इस date का एक published quiz पहले से मौजूद है. उसे Edit करें या पहले Unpublish/Draft करें.');
    }
    if(id)await updateDoc(doc(db,'quizzes',id),data);
    else await addDoc(collection(db,'quizzes'),{...data,createdAt:serverTimestamp()});
    $('quizMsg').textContent=status==='published'?'Quiz published successfully — students can attempt it now.':'Quiz draft saved.';
    clearQuizForm();await loadQuizzes();
  }catch(e){console.error(e);$('quizMsg').textContent='Quiz save error: '+(e.message||e)}
}
async function loadQuizzes(){
  const el=$('quizPosts');if(!el)return;el.innerHTML='<div class="empty">Loading quizzes…</div>';
  try{
    const snap=await getDocs(query(collection(db,'quizzes'),orderBy('updatedAt','desc')));
    const list=snap.docs.map(d=>({id:d.id,...d.data()}));
    el.innerHTML=list.map(q=>`<div class="card pad quiz-admin-row"><div><strong>${escapeHtml(q.title||'Untitled Quiz')}</strong><div class="meta">${escapeHtml(q.quizDate||'')} · ${(q.questions||[]).length} questions · ${q.durationMinutes||10} min · ${escapeHtml(q.status||'draft')}</div></div><div class="quiz-admin-actions"><button class="btn btn-dark" data-qedit="${q.id}">Edit</button>${q.status==='published'?`<button class="btn btn-light" data-qunpublish="${q.id}">Unpublish</button>`:''}<button class="btn btn-gold" data-qdelete="${q.id}">Delete</button></div></div>`).join('')||'<div class="empty">No quizzes yet.</div>';
    el.querySelectorAll('[data-qedit]').forEach(b=>b.onclick=()=>fillQuiz(list.find(q=>q.id===b.dataset.qedit)));
    el.querySelectorAll('[data-qunpublish]').forEach(b=>b.onclick=()=>unpublishQuiz(b.dataset.qunpublish));
    el.querySelectorAll('[data-qdelete]').forEach(b=>b.onclick=()=>deleteQuiz(b.dataset.qdelete));
  }catch(e){el.innerHTML='<div class="empty">Quiz list load नहीं हुई.<br>'+escapeHtml(e.message||'Firestore error')+'</div>'}
}
function fillQuiz(q){
  $('quizId').value=q.id;
  $('quizDate').value=q.quizDate||todayISO();
  $('quizDuration').value=q.durationMinutes||10;
  $('quizTestType').value=q.testType||'daily';
  $('quizMarks').value=q.marksPerQuestion??1;
  $('quizNegativeEnabled').value=q.negativeMarkingEnabled===false?'off':'on';
  $('quizNegativeNumerator').value=q.negativeNumerator??1;
  $('quizNegativeDenominator').value=q.negativeDenominator??3;
  $('quizNegativeRatio').value=(q.negativeNumerator&&q.negativeDenominator)
    ? `${q.negativeNumerator}/${q.negativeDenominator}` : '1/3';
  if(!['1/3','1/4','1/5'].includes($('quizNegativeRatio').value))
    $('quizNegativeRatio').value='custom';
  $('quizLeaderboard').value=q.leaderboardEnabled===false?'off':'on';
  $('quizShowRank').value=q.showRankAfterSubmit===false?'off':'on';
  $('quizTitle').value=q.title||'';
  $('quizDescription').value=q.description||'';
  quizQuestions=(q.questions||[]).map(x=>({question:x.question||'',options:Array.isArray(x.options)&&x.options.length===4?x.options:['','','',''],answerIndex:Number(x.answerIndex)||0,explanation:x.explanation||''}));
  renderQuizEditor();$('quizMsg').textContent='Quiz loaded for editing.';document.querySelector('.admin-quiz-box')?.scrollIntoView({behavior:'smooth',block:'start'});
}
async function unpublishQuiz(id){
  if(!confirm('इस quiz को unpublish करके draft बनाना है?'))return;
  try{
    await updateDoc(doc(db,'quizzes',id),{status:'draft',updatedAt:serverTimestamp()});
    $('quizMsg').textContent='Quiz unpublished — students इसे अब नहीं देख पाएंगे.';
    await loadQuizzes();
  }catch(e){alert(e.message||'Unpublish failed')}
}
async function deleteQuiz(id){
  if(!confirm('Delete this quiz?'))return;
  try{await deleteDoc(doc(db,'quizzes',id));await loadQuizzes()}catch(e){alert(e.message||'Delete failed')}
}
$('quizDate')?.addEventListener('focus',()=>{if(!$('quizDate').value)$('quizDate').value=todayISO()});
$('addQuizQuestion')?.addEventListener('click',()=>newQuizQuestion());
$('saveQuizDraft')?.addEventListener('click',()=>saveQuiz('draft'));
$('publishQuiz')?.addEventListener('click',()=>saveQuiz('published'));
$('clearQuiz')?.addEventListener('click',clearQuizForm);
if($('quizDate')&&!$('quizDate').value)$('quizDate').value=todayISO();
renderQuizEditor();


/* ---------------- Student Quiz Analytics ---------------- */
function formatSeconds(sec){
  sec=Number(sec)||0;
  const m=Math.floor(sec/60),s=sec%60;
  return `${m}m ${String(s).padStart(2,'0')}s`;
}
function formatStamp(v){
  try{
    if(!v)return '—';
    const d=v.toDate?v.toDate():new Date(v);
    return new Intl.DateTimeFormat('hi-IN',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(d);
  }catch{return '—'}
}
async function loadQuizAnalytics(){
  const rows=$('quizAnalyticsRows'),summary=$('quizAnalyticsSummary');
  if(!rows)return;
  try{
    // Load attempts without an orderBy query so analytics does not depend
    // on a Firestore index. Sort safely in the browser instead.
    const snap=await getDocs(collection(db,'quizAttempts'));
    console.log('QUIZ ANALYTICS: Firestore attempts fetched =', snap.size);
    const data=snap.docs
      .map(d=>({id:d.id,...d.data()}))
      .sort((a,b)=>{
        const getTime=v=>{
          try{
            if(!v)return 0;
            if(typeof v.toMillis==='function')return v.toMillis();
            if(typeof v.toDate==='function')return v.toDate().getTime();
            const t=new Date(v).getTime();
            return Number.isFinite(t)?t:0;
          }catch{return 0}
        };
        return getTime(b.startedAt)-getTime(a.startedAt);
      })
      .slice(0,500);
    const submitted=data.filter(x=>x.status==='submitted');
    const avgScore=submitted.length?Math.round(submitted.reduce((a,x)=>a+(Number(x.right)||0),0)/submitted.length):0;
    const avgScroll=data.length?Math.round(data.reduce((a,x)=>a+(Number(x.maxScrollPercent)||0),0)/data.length):0;
    const completed=submitted.length;
    const started=data.length;
    const uniqueStudents=new Set(data.map(x=>x.studentUid).filter(Boolean)).size;

    summary.innerHTML=`
      <div><strong>${started}</strong><span>Test Starts</span></div>
      <div><strong>${completed}</strong><span>Submitted</span></div>
      <div><strong>${uniqueStudents}</strong><span>Students</span></div>
      <div><strong>${avgScroll}%</strong><span>Avg Max Scroll</span></div>`;

    rows.innerHTML=data.length?data.map(x=>`
      <tr style="border-top:1px solid #e2e8f0">
        <td style="padding:10px"><strong>${escapeHtml(x.studentName||'Anonymous Student')}</strong><br><small>${escapeHtml((x.studentUid||'').slice(0,12))}</small></td>
        <td style="padding:10px">${escapeHtml(x.quizTitle||'Daily Quiz')}<br><small>${escapeHtml(x.quizDate||'')}</small></td>
        <td style="padding:10px"><strong>${x.status==='submitted'?`${Number(x.right)||0}/${Number(x.total)||0}`:'—'}</strong><br><small>${Number(x.wrong)||0} wrong · ${Number(x.skipped)||0} skipped</small></td>
        <td style="padding:10px">${x.status==='submitted'?(Number(x.accuracy)||0)+'%':'—'}</td>
        <td style="padding:10px">${formatSeconds(x.timeSpentSeconds)}</td>
        <td style="padding:10px"><strong>${Number(x.maxScrollPercent)||0}%</strong></td>
        <td style="padding:10px">${escapeHtml(x.status||'started')}</td>
        <td style="padding:10px">${formatStamp(x.submittedAt||x.startedAt)}</td>
      </tr>`).join(''):'<tr><td colspan="8" style="padding:15px">अभी कोई student attempt नहीं है.</td></tr>';
  }catch(e){
    console.error('QUIZ ANALYTICS FIRESTORE ERROR:', e);
    const msg=String(e?.message||e||'Unknown Firestore error');
    rows.innerHTML=`<tr><td colspan="8" style="padding:15px;color:#b91c1c">
      <strong>Analytics load नहीं हुई</strong><br>
      ${escapeHtml(msg)}
    </td></tr>`;
  }
}

const AI_PROMPT=`You are the senior Hindi editorial assistant for Exam Darpan, an independent Indian education and government-job information portal.

Write a publication-quality Hindi article using ONLY the official source text supplied by the editor.

FACTUAL RULES:
- The supplied official notification/source is the factual authority.
- Never invent, guess, infer, or autocomplete dates, vacancy numbers, post names, fees, age limits, eligibility, salary, selection process, exam dates, results, syllabus details, URLs, department names, or government affiliation.
- If a fact is not in the supplied source, omit it. Never fill gaps from memory.
- Preserve exact numbers, dates, post names and official URLs from the source.
- If the source is unclear or contradictory, clearly mark the issue for human verification.
- Never say Exam Darpan is an official government website.

HUMAN WRITING:
- Natural, fluent Indian Hindi for students and job seekers.
- Vary sentence structure; avoid repetitive AI templates.
- No fake excitement, clickbait, filler, or unsupported claims.
- Use short paragraphs and useful headings.
- Use tables/lists only where they genuinely make information easier to understand.
- Include only sections supported by the source: important dates, vacancy, eligibility, age limit, fee, selection process, exam pattern/syllabus, application steps, documents, important links, FAQs, etc.
- Do not make the article longer just to make it longer.

OUTPUT:
Return HTML only using h2,h3,p,ul,ol,li,strong,table,thead,tbody,tr,th,td,a.
Start with: “AI-assisted draft — Human verification required before publication.”
End with a concise official-source verification note.
Do not publish automatically.`;

$('aiGenerate').onclick=async()=>{
  const m=$('aiMsg'),topic=$('aiTopic').value.trim(),source=$('aiSource').value.trim(),btn=$('aiGenerate');
  if(!uid){m.textContent='Admin session verify नहीं हुआ.';return}
  if(!topic||!source){m.textContent='Topic और official source text दोनों भरना जरूरी है.';return}
  btn.disabled=true;btn.textContent='Generating Draft…';m.textContent='Gemini article draft तैयार कर रही है…';
  try{
    const result=await model.generateContent(`${AI_PROMPT}\n\nTOPIC:\n${topic}\n\nOFFICIAL SOURCE TEXT:\n${source}`);
    const text=result?.response?.text?.()||'';
    if(!text.trim())throw new Error('Gemini ने empty response दिया.');
    $('content').value=cleanContent(text);
    if(!$('title').value.trim())$('title').value=topic;
    if(!$('slug').value.trim())$('slug').value=slugify(topic);
    if(!$('excerpt').value.trim()){
      const plain=$('content').value.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').replace(/^AI-assisted draft — Human verification required before publication\.?/i,'').trim();
      $('excerpt').value=plain.slice(0,155).trim();
    }
    m.textContent='Draft तैयार है. अब पूरा article और official facts verify करके Save Draft या Publish करें.';
    $('content').scrollIntoView({behavior:'smooth',block:'center'});
  }catch(e){
    console.error(e);
    m.textContent='Gemini error: '+(e?.message||e);
  }finally{btn.disabled=false;btn.textContent='Generate Draft with Gemini'}
};

/* Free-plan thumbnail: no Gemini Image API, no Blaze required.
   It creates a lightweight branded SVG thumbnail locally from the article title. */
$('aiImageGenerate').onclick=()=>{
  const title=$('title').value.trim()||$('aiTopic').value.trim();
  const category=$('category').value||'Latest Updates',m=$('aiImageMsg');
  if(!title){m.textContent='पहले Article Title या Topic भरें.';return}
  const safe=escapeHtml(title).slice(0,120);
  const cat=escapeHtml(category).slice(0,40);
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs>
  <rect width="1280" height="720" fill="url(#g)"/><circle cx="1080" cy="150" r="250" fill="#f59e0b" opacity=".14"/><circle cx="1160" cy="580" r="300" fill="#fff" opacity=".05"/>
  <rect x="60" y="58" rx="10" width="260" height="54" fill="#f59e0b"/><text x="82" y="94" font-family="Arial,sans-serif" font-size="25" font-weight="700" fill="#111827">${cat}</text>
  <text x="60" y="230" font-family="Arial,sans-serif" font-size="52" font-weight="800" fill="#fff">${safe}</text>
  <rect x="60" y="600" width="1160" height="2" fill="#f59e0b"/><text x="60" y="650" font-family="Arial,sans-serif" font-size="28" font-weight="700" fill="#fff">EXAM DARPAN</text><text x="290" y="650" font-family="Arial,sans-serif" font-size="22" fill="#e2e8f0">Vacancy Se Result Tak, Har Jankari Ek Jagah</text>
  </svg>`;
  const data='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
  $('image').value=data;
  $('aiImagePreview').innerHTML=`<img src="${data}" alt="${safe}" style="width:100%;border-radius:14px;border:1px solid #e2e8f0">`;
  m.textContent='Free branded thumbnail तैयार है. यह Gemini Image API का उपयोग नहीं करती, इसलिए Blaze की जरूरत नहीं.';
};
