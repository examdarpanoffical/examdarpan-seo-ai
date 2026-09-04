import{initializeApp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js';
import{getAuth,onAuthStateChanged,signOut}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js';
import{getFirestore,doc,getDoc,collection,query,orderBy,getDocs,addDoc,updateDoc,deleteDoc,serverTimestamp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js';
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
