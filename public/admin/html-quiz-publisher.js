import{initializeApp,getApps,getApp}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js';
import{getAuth,onAuthStateChanged}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js';
import{getFirestore,doc,getDoc}from'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js';

const $=id=>document.getElementById(id);
const app=getApps().length?getApp():initializeApp(window.FIREBASE_CONFIG);
const auth=getAuth(app),db=getFirestore(app);
const endpoint=String(window.EXAMDARPAN_PUBLISH_TRIGGER_URL||'').trim();
let adminReady=false;

onAuthStateChanged(auth,async user=>{
  adminReady=false;
  if(!user)return;
  try{
    const snap=await getDoc(doc(db,'admins',user.uid));
    adminReady=snap.exists();
    if(!adminReady)throw new Error('Admin authorization failed.');
    $('htmlQuizAuth').textContent='Admin verified';
  }catch(e){
    $('htmlQuizAuth').textContent=e.message||'Admin verification failed';
  }
});

function slugify(s){
  return String(s||'').toLowerCase().normalize('NFKD')
    .replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,90);
}
function setMessage(message,isError=false){
  const el=$('htmlQuizMsg');el.textContent=message;
  el.style.color=isError?'#b91c1c':'#166534';
}
$('htmlQuizTitle')?.addEventListener('input',()=>{
  if(!$('htmlQuizSlug').dataset.edited)$('htmlQuizSlug').value=slugify($('htmlQuizTitle').value);
});
$('htmlQuizSlug')?.addEventListener('input',()=>{$('htmlQuizSlug').dataset.edited='1'});

$('publishHtmlQuiz')?.addEventListener('click',async()=>{
  const button=$('publishHtmlQuiz');
  try{
    if(!auth.currentUser||!adminReady)throw new Error('Admin login/permission verify नहीं हुआ।');
    if(!endpoint)throw new Error('Secure publish Worker URL configure नहीं है।');
    const file=$('htmlQuizFile').files?.[0];
    const title=$('htmlQuizTitle').value.trim();
    const slug=slugify($('htmlQuizSlug').value);
    if(!file||!file.name.toLowerCase().endsWith('.html'))throw new Error('एक .html file चुनें।');
    if(file.size>1500000)throw new Error('HTML file 1.5 MB से छोटी होनी चाहिए।');
    if(!title||slug.length<3)throw new Error('Quiz title और कम से कम 3 अक्षर वाला slug जरूरी है।');
    const html=await file.text();
    if(!/^\s*(<!doctype\s+html|<html)/i.test(html))throw new Error('यह पूरी HTML document file नहीं लगती।');
    button.disabled=true;button.textContent='GitHub पर Publish हो रहा है…';
    setMessage('HTML GitHub public folder में save हो रही है…');
    const token=await auth.currentUser.getIdToken();
    const response=await fetch(endpoint,{
      method:'POST',
      headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},
      body:JSON.stringify({action:'publish-html-quiz',title,slug,html})
    });
    const responseText=await response.text();
    let result={};
    try{result=JSON.parse(responseText)}catch(_){}
    if(result.queued===true&&!result.published){
      throw new Error('Worker ने पुराना SEO workflow response दिया (HTTP '+response.status+'). Live Cloudflare Worker में publish-html-quiz वाला नया worker.js deploy नहीं है। GitHub workflow चलाने से quiz publish नहीं होगी।');
    }
    if(!response.ok||!result.published){
      const detail=result.error||result.message||responseText.slice(0,240)||'कोई response detail नहीं मिली';
      throw new Error('Publish failed (HTTP '+response.status+'): '+detail);
    }
    const url=result.url;
    const link=document.createElement('a');
    link.href=url;link.target='_blank';link.rel='noopener';link.textContent=url;
    $('htmlQuizPublishedUrl').replaceChildren(link);
    $('htmlQuizCopyLink').disabled=false;
    $('htmlQuizCopyLink').onclick=async()=>{await navigator.clipboard.writeText(url);setMessage('Quiz link copied. WhatsApp पर share कर सकते हो।')};
    setMessage('GitHub पर Quiz commit हो गया। Firebase Hosting deployment पूरा होने के बाद यह URL LIVE होगा।');
  }catch(e){setMessage(e.message||String(e),true)}
  finally{button.disabled=false;button.textContent='Publish Static HTML Quiz'}
});
