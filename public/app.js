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

function getStaticPostsFromDOM(){
  const container=$('#postsContainer');

  if(!container) return [];

  return [...container.querySelectorAll('article.post')]
    .map((article,index)=>{
      const titleEl=article.querySelector('h2 a');
      const excerptEl=article.querySelector('.post-copy > p');
      const badgeEl=article.querySelector('.badge');
      const metaEls=article.querySelectorAll('.post-meta span');
      const href=
        titleEl?.getAttribute('href') ||
        article.querySelector('.read-more')?.getAttribute('href') ||
        '';

      const slug=String(href||'')
        .replace(/^\//,'')
        .split('?')[0]
        .split('#')[0];

      return {
        id:`static-${index}`,
        title:titleEl?.textContent?.trim()||'',
        slug:decodeURIComponent(slug),
        category:badgeEl?.textContent?.trim()||'',
        excerpt:excerptEl?.textContent?.trim()||'',
        content:excerptEl?.textContent?.trim()||'',
        publishedAt:metaEls[0]?.textContent?.trim()||''
      };
    })
    .filter(p=>p.title && p.slug);
}

function getMatrixPosts(){
  const firestorePosts=Array.isArray(posts)?posts:[];

  // The article grid is the final visible source of truth after render().
  // It already contains the category badge and canonical article URL.
  const container=$('#postsContainer');

  const domPosts=container
    ? [...container.querySelectorAll('article.post')]
        .map((article,index)=>{
          const titleEl=article.querySelector('h2 a');
          const excerptEl=article.querySelector('.post-copy > p');
          const badgeEl=article.querySelector('.badge');
          const href=
            titleEl?.getAttribute('href') ||
            article.querySelector('.read-more')?.getAttribute('href') ||
            '';

          const slug=String(href||'')
            .replace(/^\//,'')
            .split('?')[0]
            .split('#')[0];

          return {
            id:`dom-${index}`,
            title:titleEl?.textContent?.trim()||'',
            slug:decodeURIComponent(slug),
            category:badgeEl?.textContent?.trim()||'',
            excerpt:excerptEl?.textContent?.trim()||'',
            content:excerptEl?.textContent?.trim()||'',
            publishedAt:
              article.querySelector('.post-meta span')?.textContent?.trim()||''
          };
        })
        .filter(p=>p.title && p.slug)
    : [];

  // Prefer Firestore records because they contain the full article body,
  // but use the visible DOM category/title/slug as a reliable fallback.
  if(firestorePosts.length){
    const domBySlug=new Map(domPosts.map(p=>[p.slug,p]));

    return firestorePosts.map(p=>{
      const slug=String(p.slug||'').replace(/^\//,'');
      const dom=domBySlug.get(slug)||{};

      return {
        ...dom,
        ...p,
        slug:p.slug||dom.slug,
        title:p.title||dom.title,
        category:p.category||dom.category,
        excerpt:p.excerpt||dom.excerpt,
        content:p.content||dom.content,
        publishedAt:p.publishedAt||dom.publishedAt
      };
    });
  }

  return domPosts;
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

    let snap;

    try{
      const q=query(
        collection(db,'posts'),
        where('status','==','published'),
        orderBy('publishedAt','desc'),
        limit(60)
      );

      snap=await getDocs(q);
    }catch(queryError){
      console.warn(
        'Ordered posts query failed; using published-only fallback:',
        queryError
      );

      const fallbackQuery=query(
        collection(db,'posts'),
        where('status','==','published'),
        limit(60)
      );

      snap=await getDocs(fallbackQuery);
    }

    posts=snap.docs.map(d=>({
      id:d.id,
      ...d.data()
    }));

    // If Firestore has no usable published posts, use the
    // already-rendered static article cards as the source.
    if(!posts.length){
      posts=getStaticPostsFromDOM();
    }

    postsLoaded=true;
    postsLoadFailed=false;

    render();
  }catch(e){
    console.error('Posts load failed:',e);

    posts=getStaticPostsFromDOM();
    postsLoaded=true;
    postsLoadFailed=!posts.length;

    if(posts.length){
      render();
    }else{
      renderMatrix();
    }
  }
}

function render(){
  const search=($('#searchInput')?.value||'').toLowerCase().trim();
  const cat=window.currentCategory||'All';

  let list=posts.filter(
    p=>cat==='All' ||
      (cat==='Rajasthan Jobs'
        ? isRajasthanPost(p)
        : displayCategory(p)===cat)
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

    const rajasthanHub = isRajasthanPost(p)
      ? '<a class="post-category-link" href="/rajasthan-government-jobs">Rajasthan Jobs Hub →</a>'
      : '';

    return `
      <article class="card post ${featured?'featured-post':''}">
        <div class="post-top">
          <div class="post-copy">
            <span class="badge">${esc(displayCategory(p))}</span>

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

            ${rajasthanHub}

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

function displayCategory(p={}){
  const text=postText(p);

  if(categoryMatch(p,'admit')){
    return 'Admit Card';
  }

  if(categoryMatch(p,'results')){
    return 'Results';
  }

  if(/\b(answer key|answer-key|उत्तर कुंजी|उत्तरकुंजी)\b/i.test(text)){
    return 'Answer Key';
  }

  if(/\b(syllabus|पाठ्यक्रम|सिलेबस)\b/i.test(text)){
    return 'Syllabus';
  }

  if(isRajasthanPost(p)){
    return 'Rajasthan Jobs';
  }

  return 'Government Jobs';
}

function postText(p={}){
  return `${p.title||''} ${p.category||''} ${(p.tags||[]).join(' ')} ${p.excerpt||''} ${p.content||''}`.toLowerCase();
}

function isRajasthanPost(p={}){
  const text=postText(p);
  const category=String(p.category||'').toLowerCase();

  // Explicit Rajasthan category is useful only when the article itself
  // also contains a Rajasthan signal. This prevents SSC JE etc. from
  // leaking into Rajasthan just because an old CMS badge was wrong.
  const rajasthanSignal=
    /\b(rajasthan|rpsc|rssb|rsmssb|reet|rajasthan police|rajasthan cet|rvunl|anuprati)\b|राजस्थान|अनुप्रति/i
      .test(text);

  if(!rajasthanSignal) return false;

  return true;
}

function toDateValue(v){
  if(!v) return null;

  try{
    if(v instanceof Date){
      return isNaN(v.getTime()) ? null : v;
    }

    if(typeof v === 'object' && typeof v.toDate === 'function'){
      const d=v.toDate();
      return isNaN(d.getTime()) ? null : d;
    }

    if(typeof v === 'number'){
      const d=new Date(v);
      return isNaN(d.getTime()) ? null : d;
    }

    if(typeof v === 'string'){
      const raw=v.trim();

      if(!raw) return null;

      // Date-only YYYY-MM-DD → local calendar date.
      const ymd=raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);

      if(ymd){
        return makeDate(ymd[3],ymd[2],ymd[1]);
      }

      // ISO date-time / timezone-aware strings.
      const iso=new Date(raw);

      if(!isNaN(iso.getTime())){
        return iso;
      }

      // Controlled DD-MM-YYYY / DD/MM/YYYY / DD.MM.YYYY
      const m=raw.match(
        /^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})$/
      );

      if(m){
        const day=Number(m[1]);
        const month=Number(m[2]);
        const year=Number(m[3]);

        const d=new Date(year,month-1,day);

        if(
          d.getFullYear()===year &&
          d.getMonth()===month-1 &&
          d.getDate()===day
        ){
          return d;
        }
      }
    }
  }catch{}

  return null;
}

function makeDate(day,month,year){
  const d=new Date(
    Number(year),
    Number(month)-1,
    Number(day)
  );

  if(
    isNaN(d.getTime()) ||
    d.getFullYear()!==Number(year) ||
    d.getMonth()!==Number(month)-1 ||
    d.getDate()!==Number(day)
  ){
    return null;
  }

  return d;
}

function extractExplicitDeadline(text){
  const source=String(text||'').replace(/\s+/g,' ').trim();

  const months={
    जनवरी:1,फरवरी:2,मार्च:3,अप्रैल:4,मई:5,जून:6,
    जुलाई:7,अगस्त:8,सितंबर:9,अक्टूबर:10,नवंबर:11,दिसंबर:12,
    january:1,february:2,march:3,april:4,may:5,june:6,
    july:7,august:8,september:9,october:10,november:11,december:12
  };

  const yearMatch=source.match(/\b(20\d{2})\b/);
  const contextYear=yearMatch ? Number(yearMatch[1]) : new Date().getFullYear();

  const make=(day,month,year=contextYear)=>{
    const d=makeDate(day,month,year);
    return d;
  };

  // DD/MM/YYYY / DD-MM-YYYY / DD.MM.YYYY
  const numericPatterns=[
    /(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तारीख|last\s*date|deadline|closing\s*date)[^0-9]{0,60}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i,

    /(?:apply|application|applications|form|registration)[^0-9]{0,50}(?:by|until|upto|तक)\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i
  ];

  for(const pattern of numericPatterns){
    const m=source.match(pattern);
    if(m){
      const d=makeDate(m[1],m[2],m[3]);
      if(d) return d;
    }
  }

  // "22 सितंबर 2026 तक"
  // "7 अक्टूबर 2026 तक"
  // "25 September 2026 by"
  // "Apply by 25 September 2026"
  const monthNameAfterPattern=
    /(\d{1,2})\s+(जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर|january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(20\d{2}))?[^0-9]{0,20}(?:तक|until|by)(?=\s|[.,;:!?)]|$)/i;

  const monthNameBeforePattern=
    /(?:apply|applications?|application|form|registration)[^0-9]{0,30}(?:by|until)\s*(\d{1,2})\s+(जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर|january|february|march|april|may|june|july|august|september|october|november|december)\s+(20\d{2})/i;

  const mBefore=source.match(monthNameBeforePattern);

  if(mBefore){
    const month=months[String(mBefore[2]).toLowerCase()] || months[mBefore[2]];
    if(month){
      const d=make(mBefore[1],month,mBefore[3]);
      if(d) return d;
    }
  }

  const m=source.match(monthNameAfterPattern);

  if(m){
    const month=months[String(m[2]).toLowerCase()] ||
      months[m[2]];

    if(month){
      const d=make(m[1],month,m[3]||contextYear);
      if(d) return d;
    }
  }

  // "आवेदन 10 सितंबर से 25 सितंबर 2026 तक"
  const rangePattern=
    /\d{1,2}\s+(जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर|january|february|march|april|may|june|july|august|september|october|november|december)\s+से\s+(\d{1,2})\s+(जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर|january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(20\d{2}))?\s+तक/i;

  const r=source.match(rangePattern);

  if(r){
    const month=months[String(r[3]).toLowerCase()] || months[r[3]];
    if(month){
      const d=make(r[2],month,r[4]||contextYear);
      if(d) return d;
    }
  }

  return null;
}



function getDeadline(p={}){
  // Explicit CMS/Firestore fields are authoritative.
  const direct=[
    'lastDate',
    'last_date',
    'applicationLastDate',
    'application_last_date',
    'applicationDeadline',
    'application_deadline',
    'closingDate',
    'closing_date',
    'deadline'
  ];

  for(const key of direct){
    const d=toDateValue(p[key]);

    if(d) return d;
  }

  // Conservative article fallback:
  // only accept dates explicitly associated with deadline wording.
  return extractExplicitDeadline(`
    ${p.title||''}
    ${p.excerpt||''}
    ${p.content||''}
  `);
}

function getExamDate(p={}){
  const direct=[
    'examDate',
    'exam_date',
    'examDateTime',
    'exam_date_time'
  ];

  for(const key of direct){
    const d=toDateValue(p[key]);

    if(d) return d;
  }

  const text=`
    ${p.title||''}
    ${p.excerpt||''}
    ${p.content||''}
  `;

  const patterns=[
    /(?:परीक्षा\s*तिथि|परीक्षा\s*की\s*तिथि|परीक्षा\s*तारीख)\s*(?:है|:|-)?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i,

    /(?:exam\s*date|exam\s*on|examination\s*date)\s*(?:is|:|-)?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i
  ];

  for(const pattern of patterns){
    const m=text.match(pattern);

    if(!m) continue;

    const d=makeDate(m[1],m[2],m[3]);

    if(d) return d;
  }

  return null;
}

function daysRemaining(date){
  if(!date) return null;

  const today=new Date();
  today.setHours(0,0,0,0);

  const target=new Date(date);
  target.setHours(0,0,0,0);

  return Math.ceil(
    (target.getTime()-today.getTime())/86400000
  );
}

function isLiveVacancy(p={}){
  const deadline=getDeadline(p);

  // Calendar only treats a post as live when a reliable deadline exists.
  return !!deadline && daysRemaining(deadline)>=0;
}

function categoryMatch(p,key){
  const text=postText(p);

  const rules={
    admit:/admit card|admit-card|hall ticket|exam city|call letter|प्रवेश पत्र/i,

    results:/result|results|परिणाम|रिजल्ट/i,

    rpsc:/\brpsc\b|ras\b|public service commission/i,

    rssb:/\brssb\b|\brsmssb\b|staff selection board/i,

    police:/rajasthan police|police si|sub inspector|constable.*rajasthan/i,

    cet:/rajasthan cet|cet senior secondary|cet graduation/i,

    ldc:/\bldc\b|clerk|junior assistant/i,

    je:/junior engineer|\bjen\b|\bje recruitment\b|technical recruitment|rvunl/i,

    teacher:/reet|teacher recruitment|school lecturer|grade iii teacher|third grade teacher/i,

    university:/university result|college result|विश्वविद्यालय|यूनिवर्सिटी/i
  };

  return rules[key] ? rules[key].test(text) : false;
}

function matrix(id,cat){
  const el=$('#'+id);

  if(!el) return;

  const source=getMatrixPosts();

  const arr=source
    .filter(p=>{
      if(cat==='Rajasthan Jobs'){
        return isRajasthanPost(p);
      }

      return displayCategory(p)===cat;
    })
    .slice(0,5);

  el.innerHTML=arr.map(p=>`
    <a class="matrix-item" href="${articleUrl(p.slug)}">
      <span>${esc(p.title||'Untitled')}</span>
      <small>${formatDate(p.publishedAt)}</small>
    </a>
  `).join('') || '<div class="empty">No published updates</div>';
}


function renderCareerHub(){
  document
    .querySelectorAll('.raj-career-tile[data-hub-key]')
    .forEach(tile=>{
      const key=tile.dataset.hubKey;

      const post=getMatrixPosts()
        .filter(p=>categoryMatch(p,key))
        .sort((a,b)=>{
          const ad=toDateValue(a.publishedAt)?.getTime()||0;
          const bd=toDateValue(b.publishedAt)?.getTime()||0;

          return bd-ad;
        })[0];

      if(post && post.slug){
        tile.href=articleUrl(post.slug);

        const arrow=
          tile.querySelector('.raj-career-arrow');

        if(arrow){
          arrow.textContent='→';
        }
      }
    });
}

function renderExamCalendar(){
  const el=$('#matrixExamCalendar');

  if(!el) return;

  const live=getMatrixPosts()
    .filter(p=>isRajasthanPost(p))
    .map(p=>({
      post:p,
      deadline:getDeadline(p)
    }))
    .filter(x=>x.deadline && daysRemaining(x.deadline)>=0)
    .sort((a,b)=>a.deadline-b.deadline)
    .slice(0,6);

  el.innerHTML=live.map(({post,deadline})=>{
    const days=daysRemaining(deadline);
    const exam=getExamDate(post);

    const remaining=
      days===0
        ? 'आज अंतिम दिन'
        : days===1
          ? 'कल अंतिम दिन'
          : `${days} दिन बाकी`;

    return `
      <a class="exam-calendar-item" href="${articleUrl(post.slug)}">
        <span class="exam-calendar-main">
          <strong>${esc(post.title||'Rajasthan Vacancy')}</strong>
          <small>
            Rajasthan Jobs
            ${exam ? ` • Exam ${formatDate(exam)}` : ' • Live Vacancy'}
          </small>
        </span>

        <span class="exam-calendar-date ${days<=3?'soon':''}">
          <b>${formatDate(deadline)}</b>
          <span>${remaining}</span>
        </span>
      </a>
    `;
  }).join('') ||
  '<div class="empty">अभी published articles में verified live vacancy deadline उपलब्ध नहीं है।</div>';
}

function renderMatrix(){
  matrix('matrixLatestJobs','Rajasthan Jobs');
  matrix('matrixAdmitCards','Admit Card');
  matrix('matrixResults','Results');
  renderExamCalendar();
  renderCareerHub();
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
