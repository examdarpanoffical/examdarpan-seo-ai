import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js';
import { getFirestore, collection, getDocs, query, where, orderBy, limit } from 'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js';

const app=initializeApp(window.FIREBASE_CONFIG),db=getFirestore(app);
const $=s=>document.querySelector(s);
const esc=(s='')=>String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const formatDate=v=>{try{const d=v?.toDate?v.toDate():new Date(v);return isNaN(d)?'—':new Intl.DateTimeFormat('hi-IN',{day:'2-digit',month:'short',year:'numeric'}).format(d)}catch{return '—'}};
const articleUrl=slug=>'/'+encodeURIComponent(String(slug||'').trim());
const readingTime=html=>Math.max(1,Math.ceil(String(html||'').replace(/<[^>]*>/g,' ').trim().split(/\s+/).filter(Boolean).length/180));
let posts=[];

async function loadPosts(){
  try{
    const q=query(collection(db,'posts'),where('status','==','published'),orderBy('publishedAt','desc'),limit(80));
    const snap=await getDocs(q);posts=snap.docs.map(d=>({id:d.id,...d.data()}));
  }catch(e){console.error(e);posts=[];const el=$('#postsContainer');if(el)el.innerHTML='<div class="card empty"><strong>Updates load नहीं हो पाए.</strong><br><span>'+esc(e.message||'Firestore error')+'</span></div>'}
  render();
}
function render(){
  const search=($('#searchInput')?.value||'').toLowerCase().trim(),cat=window.currentCategory||'All';
  let list=posts.filter(p=>cat==='All'||p.category===cat);
  if(search)list=list.filter(p=>`${p.title||''} ${p.category||''} ${(p.tags||[]).join(' ')}`.toLowerCase().includes(search));
  const count=$('#resultCount');if(count)count.textContent=`${list.length} ${list.length===1?'article':'articles'}`;
  const html=list.map((p,i)=>`<article class="card post ${i===0&&!search&&!cat||cat==='All'&&i===0&&!search?'featured-post':''}"><div class="post-top"><div class="post-copy"><span class="badge">${esc(p.category||'Latest Update')}</span><h2><a href="${articleUrl(p.slug)}">${esc(p.title||'Untitled')}</a></h2><p>${esc(p.excerpt||'Exam Darpan पर नवीनतम verified information पढ़ें।')}</p><div class="post-meta"><span>${formatDate(p.publishedAt)}</span><span>•</span><span>${readingTime(p.content)} min read</span></div><a class="read-more" href="${articleUrl(p.slug)}">पूरा article पढ़ें <b>→</b></a></div>${p.featuredImage?`<img loading="lazy" decoding="async" src="${esc(p.featuredImage)}" alt="${esc(p.title||'Exam Darpan article image')}">`:''}</div></article>`).join('');
  $('#postsContainer').innerHTML=html||'<div class="card empty"><strong>इस category में अभी कोई published update नहीं है।</strong><br>दूसरी category या search try करें.</div>';renderMatrix();
}
function matrix(id,cat){const el=$('#'+id);if(!el)return;const arr=posts.filter(p=>p.category===cat).slice(0,5);const data=arr.length?arr:posts.slice(0,5);el.innerHTML=data.map(p=>`<a class="matrix-item" href="${articleUrl(p.slug)}"><span>${esc(p.title||'Untitled')}</span><small>${formatDate(p.publishedAt)}</small></a>`).join('')||'<div class="empty">No updates</div>'}
function renderMatrix(){matrix('matrixLatestJobs','Rajasthan Jobs');matrix('matrixAdmitCards','Admit Card');matrix('matrixResults','Results');}
window.setCategory=c=>{window.currentCategory=c;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.cat===c));render();if(location.search!==`?category=${encodeURIComponent(c)}`&&c!=='All')history.replaceState({},'',`?category=${encodeURIComponent(c)}`);};
window.handleSearch=()=>{render();const q=$('#searchInput')?.value.trim();history.replaceState({},'',q?`?q=${encodeURIComponent(q)}`:window.currentCategory&&window.currentCategory!=='All'?`?category=${encodeURIComponent(window.currentCategory)}`:'/')};
function boot(){document.querySelectorAll('[data-year]').forEach(x=>x.textContent=new Date().getFullYear());loadPosts();}
boot();
