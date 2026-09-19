(()=>{
  const V='12.5.0'; let mods;
  const $=id=>document.getElementById(id);

  async function fb(){
    if(mods)return mods;
    const [app,auth,fs]=await Promise.all([
      import(`https://www.gstatic.com/firebasejs/${V}/firebase-app.js`),
      import(`https://www.gstatic.com/firebasejs/${V}/firebase-auth.js`),
      import(`https://www.gstatic.com/firebasejs/${V}/firebase-firestore.js`)
    ]);
    const a=app.getApps().length?app.getApp():app.initializeApp(window.FIREBASE_CONFIG);
    return mods={auth:auth.getAuth(a),db:fs.getFirestore(a),...fs};
  }

  function panel(){
    if(!$('quizQuestions')||$('quiz-control-panel'))return;

    const x=document.createElement('div');
    x.id='quiz-control-panel';
    x.className='card pad';
    x.style.cssText='margin:16px 0;border:1px solid #dbeafe;background:#f8fbff';

    x.innerHTML=`
      <div class="section-label">QUIZ CONTROLS</div>
      <h3 style="margin:6px 0 4px">Scoring, Result &amp; Leaderboard Controls</h3>
      <p class="meta">
        हर quiz के साथ save होंगे। पुराने quizzes के लिए safe defaults:
        negative marking ON, leaderboard ON, rank ON.
      </p>

      <div class="admin-form-grid">

        <div class="field">
          <label>Marks per Question</label>
          <input id="quizMarksPerQuestion"
                 type="number"
                 min="0.01"
                 step="0.01"
                 value="1">
        </div>

        <div class="field">
          <label>Negative Marking</label>
          <select id="quizNegativeEnabled">
            <option value="true">ON</option>
            <option value="false">OFF</option>
          </select>
        </div>

        <div class="field">
          <label>Negative Numerator</label>
          <input id="quizNegativeNumerator"
                 type="number"
                 min="0"
                 step="0.01"
                 value="1">
        </div>

        <div class="field">
          <label>Negative Denominator</label>
          <input id="quizNegativeDenominator"
                 type="number"
                 min="0.01"
                 step="0.01"
                 value="3">
        </div>

      </div>

      <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:10px">

        <label>
          <input id="quizLeaderboardEnabled"
                 type="checkbox"
                 checked>
          <strong>Public Leaderboard ON</strong>
        </label>

        <label>
          <input id="quizShowRankAfterSubmit"
                 type="checkbox"
                 checked>
          <strong>Show Rank After Submit</strong>
        </label>

      </div>

      <p id="quizControlMsg"
         class="meta"
         style="margin-top:10px"></p>
    `;

    $('quizQuestions').before(x);
    defaults();
  }

  function defaults(q={}){
    if(!$('quiz-control-panel'))return;

    const n=Number(q.marksPerQuestion);
    const a=Number(q.negativeNumerator);
    const b=Number(q.negativeDenominator);

    $('quizMarksPerQuestion').value =
      Number.isFinite(n)&&n>0?n:1;

    $('quizNegativeEnabled').value =
      q.negativeMarkingEnabled===false?'false':'true';

    $('quizNegativeNumerator').value =
      Number.isFinite(a)&&a>=0?a:1;

    $('quizNegativeDenominator').value =
      Number.isFinite(b)&&b>0?b:3;

    $('quizLeaderboardEnabled').checked =
      q.leaderboardEnabled!==false;

    $('quizShowRankAfterSubmit').checked =
      q.showRankAfterSubmit!==false;
  }

  function questions(){
    return [...document.querySelectorAll('.quiz-admin-question')].map(c=>({
      question:
        c.querySelector('textarea[data-qfield$=":question"]')
          ?.value.trim()||'',

      options:
        [...c.querySelectorAll('input[data-qfield*="option:"]')]
          .map(x=>x.value.trim()),

      answerIndex:
        Number(
          c.querySelector('select[data-qfield$=":answer"]')
            ?.value||0
        ),

      explanation:
        c.querySelector('textarea[data-qfield$=":explanation"]')
          ?.value.trim()||''
    }));
  }

  async function save(status){
    const msg=$('quizControlMsg')||$('quizMsg');

    try{
      const f=await fb();

      if(!f.auth.currentUser)
        throw Error('Admin session verify नहीं हुआ.');

      const admin=await f.getDoc(
        f.doc(f.db,'admins',f.auth.currentUser.uid)
      );

      if(!admin.exists())
        throw Error('Admin authorization failed.');

      const qs=questions();
      const date=$('quizDate').value;

      if(
        !date ||
        !qs.length ||
        qs.some(q=>
          !q.question ||
          q.options.length!==4 ||
          q.options.some(x=>!x)
        )
      ){
        throw Error(
          'Quiz date और हर question के चारों options जरूरी हैं.'
        );
      }

      const marks=Math.max(
        .01,
        Number($('quizMarksPerQuestion').value)||1
      );

      const num=Math.max(
        0,
        Number($('quizNegativeNumerator').value)
      );

      const den=Math.max(
        .01,
        Number($('quizNegativeDenominator').value)||3
      );

      const data={
        title:
          $('quizTitle').value.trim()||
          `Daily Quiz — ${date}`,

        description:
          $('quizDescription').value.trim(),

        quizDate:date,

        durationMinutes:
          Math.min(
            180,
            Math.max(
              1,
              Number($('quizDuration').value)||10
            )
          ),

        marksPerQuestion:marks,

        negativeMarkingEnabled:
          $('quizNegativeEnabled').value!=='false',

        negativeNumerator:num,
        negativeDenominator:den,

        leaderboardEnabled:
          $('quizLeaderboardEnabled').checked,

        showRankAfterSubmit:
          $('quizShowRankAfterSubmit').checked,

        questions:qs,
        status,
        updatedAt:f.serverTimestamp()
      };

      const id=$('quizId').value;

      if(status==='published'){
        const s=await f.getDocs(
          f.query(
            f.collection(f.db,'quizzes'),
            f.where('status','==','published'),
            f.where('quizDate','==',date),
            f.limit(5)
          )
        );

        if(s.docs.some(d=>d.id!==id)){
          throw Error(
            'इस date का एक published quiz पहले से मौजूद है.'
          );
        }
      }

      if(id){
        await f.updateDoc(
          f.doc(f.db,'quizzes',id),
          data
        );
      }else{
        await f.addDoc(
          f.collection(f.db,'quizzes'),
          {
            ...data,
            createdAt:f.serverTimestamp()
          }
        );
      }

      msg.textContent =
        status==='published'
          ? 'Quiz published with controls saved.'
          : 'Quiz draft saved with controls.';

      setTimeout(()=>location.reload(),250);

    }catch(e){
      console.error(
        '[ExamDarpan quiz controls]',
        e
      );

      msg.textContent=
        'Quiz save error: '+(e.message||e);
    }
  }

  /*
   * Capture phase:
   * dashboard.js का existing onclick आने से पहले
   * हमारा controlled save चलेगा.
   */
  document.addEventListener('click',e=>{

    const b=e.target.closest?.(
      '#saveQuizDraft,#publishQuiz'
    );

    if(b){
      e.preventDefault();
      e.stopImmediatePropagation();

      save(
        b.id==='publishQuiz'
          ? 'published'
          : 'draft'
      );

      return;
    }

    /*
     * Existing quiz Edit करने पर उसके saved controls
     * वापस UI में load करें.
     */
    const edit=e.target.closest?.('[data-qedit]');

    if(edit){

      setTimeout(async()=>{
        try{
          const f=await fb();

          const s=await f.getDoc(
            f.doc(
              f.db,
              'quizzes',
              edit.dataset.qedit
            )
          );

          if(s.exists())
            defaults(s.data());

        }catch(err){
          console.warn(
            '[ExamDarpan quiz controls]',
            err
          );
        }
      },350);
    }

  },true);

  function start(){
    panel();
    defaults();
  }

  if(document.readyState==='loading'){
    document.addEventListener(
      'DOMContentLoaded',
      start,
      {once:true}
    );
  }else{
    start();
  }

})();
