let app=null,db=null;
let posts=[];
let postsLoaded=false;
let postsLoadFailed=false;

const $=s=>document.querySelector(s);

const esc=(s='')=>String(s).replace(/[&<>'"]/g,c=>({
  '&':'&amp;',
  '<':'&lt;',
  '>':'&gt;',
  "'":'&#39;',
  '"':'&quot;'
}[c]));

const formatDate=v=>{
  try{
    const d=v?.toDate?v.toDate():new Date(v);
    return isNaN(d)
      ? '—'
      : new Intl.DateTimeFormat('hi-IN',{
          day:'2-digit',
          month:'short',
          year:'numeric'
        }).format(d);
  }catch{
    return '—';
  }
};

const articleUrl=slug=>'/'+encodeURIComponent(String(slug||'').trim());

const readingTime=html=>{
  const text=String(html||'')
    .replace(/<[^>]*>/g,' ')
    .trim();

  const words=text?text.split(/\s+/).length:0;
  return Math.max(1,Math.ceil(words/180));
};

async function loadFirebase(){
  if(db) return db;

  const [{initializeApp},{getFirestore,collection,getDocs,query,where,orderBy,limit}]=await Promise.all([
    import('https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js'),
    import('https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js')
  ]);

  app=initializeApp(window.FIREBASE_CONFIG);
  db=getFirestore(app);

  window.__ED_FIREBASE={
    collection,
    getDocs,
    query,
    where,
    orderBy,
    limit
  };

  return db;
}

async function loadPosts(){
  try{
    await loadFirebase();

    const {
      collection,
      getDocs,
      query,
      where,
      orderBy,
      limit
    }=window.__ED_FIREBASE;

    const q=query(
      collection(db,'posts'),
      where('status','==','published'),
      orderBy('publishedAt','desc'),
      limit(36)
    );

    const snap=await getDocs(q);

    posts=snap.docs.map(d=>({
      id:d.id,
      ...d.data()
    }));

    postsLoaded=true;
    postsLoadFailed=false;

    render();
  }catch(e){
    console.error('Posts load failed:',e);

    posts=[];
    postsLoaded=true;
    postsLoadFailed=true;

    const el=$('#postsContainer');

    if(el && !el.querySelector('[href]')){
      el.innerHTML=
        '<div class="card empty">'+
        '<strong>Updates अभी load नहीं हो पाए.</strong><br>'+
        '<span>'+esc(e.message||'Firestore error')+'</span>'+
        '</div>';
    }

    renderMatrix();
  }
}

function render(){
  const search=($('#searchInput')?.value||'').toLowerCase().trim();
  const cat=window.currentCategory||'All';

  let list=posts.filter(
    p=>cat==='All'||p.category===cat
  );

  if(search){
    list=list.filter(p=>
      `${p.title||''} ${p.category||''} ${(p.tags||[]).join(' ')}`
        .toLowerCase()
        .includes(search)
    );
  }

  const count=$('#resultCount');

  if(count){
    count.textContent=
      `${list.length} ${list.length===1?'article':'articles'}`;
  }

  const container=$('#postsContainer');

  if(postsLoadFailed && container && !search && cat==='All'){
    renderMatrix();
    return;
  }

  if(!postsLoaded && container && !search && cat==='All'){
    renderMatrix();
    return;
  }

  const html=list.map((p,i)=>{
    const featured=
      i===0 &&
      !search &&
      cat==='All';

    const image=p.featuredImage
      ? `<img loading="lazy" decoding="async" src="${esc(p.featuredImage)}" alt="${esc(p.title||'Exam Darpan article image')}">`
      : '';

    return `
      <article class="card post ${featured?'featured-post':''}">
        <div class="post-top">
          <div class="post-copy">
            <span class="badge">${esc(p.category||'Latest Update')}</span>

            <h2>
              <a href="${articleUrl(p.slug)}">
                ${esc(p.title||'Untitled')}
              </a>
            </h2>

            <p>
              ${esc(
                p.excerpt ||
                'Exam Darpan पर नवीनतम verified information पढ़ें।'
              )}
            </p>

            <div class="post-meta">
              <span>${formatDate(p.publishedAt)}</span>
              <span>•</span>
              <span>${readingTime(p.content)} min read</span>
            </div>

            <a class="read-more" href="${articleUrl(p.slug)}">
              पूरा article पढ़ें <b>→</b>
            </a>
          </div>

          ${image}
        </div>
      </article>
    `;
  }).join('');

  if(container){
    container.innerHTML=
      html ||
      '<div class="card empty">'+
      '<strong>इस category में अभी कोई published update नहीं है।</strong><br>'+
      'दूसरी category या search try करें.'+
      '</div>';
  }

  renderMatrix();
}

function matrix(id,cat){
  const el=$('#'+id);

  if(!el) return;

  const arr=posts
    .filter(p=>p.category===cat)
    .slice(0,5);

  el.innerHTML=arr.map(p=>`
    <a class="matrix-item" href="${articleUrl(p.slug)}">
      <span>${esc(p.title||'Untitled')}</span>
      <small>${formatDate(p.publishedAt)}</small>
    </a>
  `).join('') || '<div class="empty">No updates</div>';
}

function renderMatrix(){
  matrix('matrixLatestJobs','Rajasthan Jobs');
  matrix('matrixAdmitCards','Admit Card');
  matrix('matrixResults','Results');
}

window.setCategory=c=>{
  window.currentCategory=c;

  document.querySelectorAll('.tab').forEach(x=>{
    x.classList.toggle('active',x.dataset.cat===c);
  });

  render();

  const next=
    c!=='All'
      ? `?category=${encodeURIComponent(c)}`
      : '/';

  if(location.search!==next){
    history.replaceState({},'',next);
  }
};

window.handleSearch=()=>{
  render();

  const q=$('#searchInput')?.value.trim();

  history.replaceState(
    {},
    '',
    q
      ? `?q=${encodeURIComponent(q)}`
      : window.currentCategory &&
        window.currentCategory!=='All'
          ? `?category=${encodeURIComponent(window.currentCategory)}`
          : '/'
  );
};

async function loadDailyQuiz(){
  const meta=$('#dailyQuizMeta');
  const cta=$('#dailyQuizCta');
  const summary=$('#dailyQuizSummary');

  if(!meta) return;

  try{
    await loadFirebase();

    const {
      collection,
      getDocs,
      query,
      where,
      limit
    }=window.__ED_FIREBASE;

    const now=new Date();

    const y=now.getFullYear();
    const m=String(now.getMonth()+1).padStart(2,'0');
    const d=String(now.getDate()).padStart(2,'0');

    const today=`${y}-${m}-${d}`;

    const q=query(
      collection(db,'quizzes'),
      where('status','==','published'),
      where('quizDate','==',today),
      limit(1)
    );

    const snap=await getDocs(q);
    const docSnap=snap.docs[0];

    if(!docSnap){
      meta.textContent=
        'आज का quiz अभी publish नहीं हुआ है।';

      cta.textContent='Previous Quizzes →';
      cta.href='/quiz.html#previous';

      return;
    }

    const quiz=docSnap.data();

    const count=
      Array.isArray(quiz.questions)
        ? quiz.questions.length
        : 0;

    meta.textContent=
      `${count} Questions • ${quiz.durationMinutes||10} Minutes`;

    cta.textContent='Start Today’s Quiz →';

    cta.href=
      `/quiz.html?id=${encodeURIComponent(docSnap.id)}`;

    if(summary){
      summary.textContent=
        quiz.description ||
        'Timer के साथ quiz दें और submit करने के बाद score, सही-गलत answers और explanations देखें।';
    }

  }catch(e){
    console.warn('Daily quiz unavailable',e);

    meta.textContent=
      'आज का quiz check करने के लिए खोलें।';
  }
}

function updateYear(){
  const year=new Date().getFullYear();

  document.querySelectorAll('[data-year]').forEach(x=>{
    x.textContent=year;
  });
}

function startNonCriticalWork(){
  updateYear();

  const run=()=>{
    loadPosts();
    loadDailyQuiz();
  };

  if('requestIdleCallback' in window){
    requestIdleCallback(run,{timeout:1200});
  }else{
    setTimeout(run,120);
  }
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',startNonCriticalWork,{
    once:true
  });
}else{
  startNonCriticalWork();
}
