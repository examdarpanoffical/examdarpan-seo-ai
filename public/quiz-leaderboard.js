(function () {
  const path = location.pathname.replace(/\/+$/, '');
  if (path !== '/quiz' && path !== '/quiz.html' && path !== '') return;

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));

  const fmtScore = n => Number.isFinite(Number(n))
    ? Number(n).toFixed(2).replace(/\.00$/, '')
    : '0';

  const fmtTime = sec => {
    sec = Math.max(0, Math.round(Number(sec || 0)));
    return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
  };

  const today = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  };

  const css = `
  .ed-leaderboard{
    margin:22px 0 28px;
    padding:22px;
    border-radius:22px;
    background:linear-gradient(145deg,#fff,#f8fbff);
    border:1px solid #dbeafe;
    box-shadow:0 14px 40px rgba(15,23,42,.08)
  }
  .ed-lb-head{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:16px
  }
  .ed-lb-eyebrow{
    font-size:11px;
    letter-spacing:1.2px;
    font-weight:900;
    color:#2563eb
  }
  .ed-lb-title{
    margin:4px 0 0;
    color:#0f172a;
    font-size:24px;
    line-height:1.2
  }
  .ed-lb-live{
    padding:7px 11px;
    border-radius:999px;
    background:#ecfdf5;
    color:#047857;
    font-size:11px;
    font-weight:900
  }
  .ed-lb-self{
    display:grid;
    grid-template-columns:auto 1fr auto;
    align-items:center;
    gap:12px;
    padding:14px;
    border-radius:17px;
    background:#eff6ff;
    border:1px solid #bfdbfe;
    margin-bottom:16px
  }
  .ed-lb-rank{
    font-weight:950;
    color:#1d4ed8;
    font-size:20px;
    min-width:48px;
    text-align:center
  }
  .ed-lb-self strong{
    display:block;
    color:#0f172a;
    font-size:15px
  }
  .ed-lb-self small{
    display:block;
    margin-top:3px;
    color:#64748b;
    line-height:1.5
  }
  .ed-lb-section-title{
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin:4px 0 10px;
    color:#0f172a;
    font-weight:900
  }
  .ed-lb-section-title span{
    font-size:12px;
    color:#64748b;
    font-weight:700
  }
  .ed-lb-list{
    display:grid;
    gap:8px
  }
  .ed-lb-row{
    display:grid;
    grid-template-columns:42px 1fr auto auto;
    align-items:center;
    gap:10px;
    padding:11px 12px;
    border:1px solid #e2e8f0;
    border-radius:14px;
    background:#fff
  }
  .ed-lb-row.me{
    border-color:#93c5fd;
    background:#f8fbff
  }
  .ed-lb-pos{
    font-weight:950;
    color:#64748b;
    text-align:center
  }
  .ed-lb-name{
    font-weight:850;
    color:#0f172a;
    font-size:14px
  }
  .ed-lb-mini{
    display:block;
    margin-top:3px;
    font-size:10px;
    color:#64748b
  }
  .ed-lb-score{
    font-weight:950;
    color:#1d4ed8;
    text-align:right
  }
  .ed-lb-time{
    font-size:11px;
    color:#64748b;
    white-space:nowrap
  }
  .ed-lb-next{
    margin-top:14px;
    padding:12px 14px;
    border-radius:14px;
    background:#f8fafc;
    color:#475569;
    font-size:13px;
    line-height:1.5
  }
  @media(max-width:640px){
    .ed-leaderboard{padding:16px;margin:16px 0 22px}
    .ed-lb-title{font-size:20px}
    .ed-lb-row{grid-template-columns:32px 1fr auto}
    .ed-lb-time{display:none}
    .ed-lb-self{grid-template-columns:auto 1fr}
  }`;

  function injectStyle(){
    if(document.getElementById('ed-leaderboard-style')) return;
    const s=document.createElement('style');
    s.id='ed-leaderboard-style';
    s.textContent=css;
    document.head.appendChild(s);
  }

  async function getContext(){
    try{
      const appMod=await import(
        'https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js'
      );
      const apps=appMod.getApps();
      if(!apps.length) return null;

      const app=appMod.getApp();
      const authMod=await import(
        'https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js'
      );
      const dbMod=await import(
        'https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js'
      );

      return {
        auth:authMod.getAuth(app),
        db:dbMod.getFirestore(app),
        ...dbMod
      };
    }catch(e){
      console.warn('[ExamDarpan leaderboard] Firebase context failed',e);
      return null;
    }
  }

  function waitForAuth(auth){
    return new Promise(resolve=>{
      if(auth.currentUser) return resolve(auth.currentUser);

      let done=false;
      const finish=u=>{
        if(done)return;
        done=true;
        clearInterval(timer);
        clearTimeout(timeout);
        resolve(u||null);
      };

      const timer=setInterval(()=>{
        if(auth.currentUser) finish(auth.currentUser);
      },150);

      const timeout=setTimeout(()=>finish(null),10000);
    });
  }

  async function loadEntries(ctx, quizId){
    const {db,collection,getDocs,query,where,limit}=ctx;

    const mapRows=(snap)=>snap.docs
      .map(d=>({id:d.id,...d.data()}))
      .filter(x=>x.status==='submitted' && Number.isFinite(Number(x.score)))
      .sort((a,b)=>
        Number(b.score)-Number(a.score) ||
        Number(b.correct||b.right||0)-Number(a.correct||a.right||0) ||
        Number(a.wrong||0)-Number(b.wrong||0) ||
        Number(a.timeTakenSeconds||a.timeSpentSeconds||0)-
          Number(b.timeTakenSeconds||b.timeSpentSeconds||0) ||
        Number(a.submittedAtMs||0)-Number(b.submittedAtMs||0)
      );

    /*
     * Public leaderboard source.
     * quizLeaderboard has public read permission in firestore.rules,
     * so it can contain submissions from all students.
     */
    try{
      const snap=await getDocs(query(
        collection(db,'quizLeaderboard'),
        where('quizId','==',quizId),
        limit(1000)
      ));

      const rows=mapRows(snap);

      if(rows.length){
        const latest=new Map();

        rows.forEach(row=>{
          const key=row.studentUid||row.id;
          const prev=latest.get(key);
          const rowMs=Number(row.submittedAtMs||0);
          const prevMs=Number(prev?.submittedAtMs||0);

          if(!prev || rowMs>=prevMs){
            latest.set(key,row);
          }
        });

        return [...latest.values()].sort((a,b)=>
          Number(b.score)-Number(a.score) ||
          Number(b.correct||b.right||0)-Number(a.correct||a.right||0) ||
          Number(a.wrong||0)-Number(b.wrong||0) ||
          Number(a.timeTakenSeconds||a.timeSpentSeconds||0)-
            Number(b.timeTakenSeconds||b.timeSpentSeconds||0) ||
          Number(a.submittedAtMs||0)-Number(b.submittedAtMs||0)
        );
      }
    }catch(e){
      console.warn('[ExamDarpan leaderboard] public leaderboard read failed',e);
    }

    /*
     * Fallback: own quizAttempt. This keeps the result useful if the
     * leaderboard write was rejected or an older submission has no
     * quizLeaderboard document.
     */
    try{
      const snap=await getDocs(query(
        collection(db,'quizAttempts'),
        where('quizId','==',quizId),
        limit(1000)
      ));

      return mapRows(snap);
    }catch(e){
      console.warn('[ExamDarpan leaderboard] quizAttempts read failed',e);
      return [];
    }
  }

  function renderCard(result, user, rows){
    if(!result || !result.quizId || !rows.length) return;

    const me=rows.find(x=>x.studentUid===user.uid);
    if(!me) return;

    const rank=rows.findIndex(x=>x.studentUid===user.uid)+1;
    const top=rows.slice(0,10);

    injectStyle();

    const old=document.querySelector('.ed-leaderboard');
    if(old) old.remove();

    const card=document.createElement('section');
    card.className='ed-leaderboard';

    const maxMarks=Number(me.maxMarks||result.maxMarks||me.total||result.total||10);

    card.innerHTML=`
      <div class="ed-lb-head">
        <div>
          <div class="ed-lb-eyebrow">🏆 EXAM DARPAN LEADERBOARD</div>
          <h2 class="ed-lb-title">
            ${result.quizDate===today()?'आज की Ranking':'Test Ranking'}
          </h2>
        </div>
        <span class="ed-lb-live">● LIVE</span>
      </div>

      <div class="ed-lb-self">
        <div class="ed-lb-rank">#${rank}</div>
        <div>
          <strong>${esc(me.studentName||'Student')}</strong>
          <small>
            ${fmtScore(me.score)} / ${fmtScore(maxMarks)}
            · ${Number(me.correct??me.right??0)} सही
            · ${Number(me.wrong??0)} गलत
            · ${Number(me.skipped||0)} छोड़े
            · ⏱️ ${fmtTime(me.timeTakenSeconds||me.timeSpentSeconds)}
            ${me.negativeMarkingEnabled ? ` · −${fmtScore(me.negativeDeductionPerWrong||0)} / wrong` : ' · No negative marking'}
          </small>
        </div>
      </div>

      <div class="ed-lb-section-title">
        <span>TOP PERFORMERS</span>
        <span>${rows.length} students</span>
      </div>

      <div class="ed-lb-list">
        ${top.map((r,i)=>`
          <div class="ed-lb-row ${r.studentUid===user.uid?'me':''}">
            <div class="ed-lb-pos">
              ${i===0?'🥇':i===1?'🥈':i===2?'🥉':'#'+(i+1)}
            </div>
            <div class="ed-lb-name">
              ${esc(r.studentName||'Student')}
              ${r.studentUid===user.uid?'<span class="ed-lb-mini">YOU</span>':''}
              <span class="ed-lb-mini">
                ${Number(r.correct??r.right??0)} correct · ${Number(r.wrong??0)} wrong
              </span>
            </div>
            <div class="ed-lb-score">${fmtScore(r.score)}</div>
            <div class="ed-lb-time">⏱️ ${fmtTime(r.timeTakenSeconds)}</div>
          </div>
        `).join('')}
      </div>

      <div class="ed-lb-next">
        <b>Your Rank: #${rank}</b>
        · Ranking पहले Score, फिर Correct Answers, फिर कम Wrong और कम Time से तय होती है।
      </div>
    `;

    const resultBox=document.getElementById('quizResult');
    if(resultBox) resultBox.appendChild(card);
  }

  async function run(){
    const resultBox=document.getElementById('quizResult');
    if(!resultBox) return;

    /*
     * IMPORTANT:
     * Register the submission listener BEFORE waiting for Firebase/Auth.
     * Otherwise a fast submission can fire the event before the listener
     * exists and the leaderboard never renders.
     */
    let submissionPending=false;
    let refreshTimer=null;

    const requestRefresh=()=>{
      submissionPending=true;
      clearTimeout(refreshTimer);
      refreshTimer=setTimeout(()=>refresh(),250);
    };

    window.addEventListener('examDarpan:quizSubmitted',requestRefresh);

    let ctx=null;
    let user=null;

    // Firebase/Auth may initialize after this script.
    for(let i=0;i<40;i++){
      ctx=await getContext();

      if(ctx){
        user=await waitForAuth(ctx.auth);
        if(user) break;
      }

      await new Promise(r=>setTimeout(r,250));
    }

    if(!ctx || !user){
      console.warn('[ExamDarpan leaderboard] Firebase/Auth not ready');
      return;
    }

    let rendering=false;

    const getQuizId=()=>{
      return window.quizId ||
        document.body.dataset.quizId ||
        new URLSearchParams(location.search).get('id');
    };

    const refresh=async()=>{
      if(rendering) return;

      const quizId=getQuizId();
      if(!quizId) return;

      // Do not render before the result screen exists.
      if(resultBox.hidden) return;

      rendering=true;

      try{
        const resultData={
          quizId,
          quizDate:window.quiz?.quizDate||today(),
          maxMarks:window.quiz?.questions?.length
            ? Number(window.quiz.marksPerQuestion||1)*window.quiz.questions.length
            : 10
        };

        /*
         * Firestore write may become queryable a moment after updateDoc/addDoc.
         * Retry several times.
         */
        for(let attempt=0;attempt<10;attempt++){
          const rows=await loadEntries(ctx,quizId);

          if(rows.length){
            renderCard(resultData,user,rows);
            submissionPending=false;
            return;
          }

          await new Promise(r=>setTimeout(r,500*(attempt+1)));
        }

        console.warn(
          '[ExamDarpan leaderboard] No public leaderboard rows found:',
          quizId
        );

      }catch(e){
        console.error(
          '[ExamDarpan leaderboard] refresh failed',
          e
        );
      }finally{
        rendering=false;
      }
    };

    /*
     * If the event happened while Firebase/Auth was initializing,
     * submissionPending will be true here and we won't lose it.
     */
    if(submissionPending){
      setTimeout(refresh,100);
    }

    /*
     * Also watch the result screen. This covers:
     * - event timing races
     * - browser refresh/re-entry
     * - slower Firestore writes
     */
    const observer=new MutationObserver(()=>{
      if(!resultBox.hidden){
        clearTimeout(refreshTimer);
        refreshTimer=setTimeout(refresh,300);
      }
    });

    observer.observe(resultBox,{
      childList:true,
      subtree:true,
      attributes:true,
      attributeFilter:['hidden','class','style']
    });

    /*
     * If result is already visible when Firebase/Auth becomes ready.
     */
    if(!resultBox.hidden){
      setTimeout(refresh,300);
    }
  }

  let started=false;

  const startOnce=()=>{
    if(started)return;
    started=true;
    run();
  };

  window.addEventListener('examDarpan:firebaseReady',startOnce,{once:true});

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',startOnce,{once:true});
  }else{
    startOnce();
  }
})();
