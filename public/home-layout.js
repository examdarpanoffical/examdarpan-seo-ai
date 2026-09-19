(function () {
  'use strict';

  function moveDailyQuiz() {
    const quiz = document.getElementById('daily-quiz');
    const notificationGrid = document.querySelector('main.main > .grid3');

    if (!quiz || !notificationGrid) return;

    // Existing quiz UI/content untouched — only its dashboard position changes.
    notificationGrid.insertAdjacentElement('afterend', quiz);
  }

  function addSocialProfiles() {
    const community = document.querySelector('.ed-community-hub');
    if (!community || community.querySelector('.ed-social-follow')) return;

    const wrap = document.createElement('div');
    wrap.className = 'ed-social-follow';

    wrap.innerHTML = `
      <div class="ed-social-follow-head">
        <span>FOLLOW EXAM DARPAN</span>
        <small>हर जरूरी update से जुड़े रहें</small>
      </div>

      <div class="ed-social-grid">

        <a class="ed-social-card ed-instagram"
           href="https://www.instagram.com/examdarpan_official/"
           target="_blank"
           rel="noopener noreferrer"
           aria-label="Visit Exam Darpan on Instagram">
          <span class="ed-social-logo" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <rect x="4" y="4" width="24" height="24" rx="7"
                stroke="currentColor" stroke-width="2.4"/>
              <circle cx="16" cy="16" r="5.2"
                stroke="currentColor" stroke-width="2.4"/>
              <circle cx="23.1" cy="8.9" r="1.5"
                fill="currentColor"/>
            </svg>
          </span>
          <span>
            <strong>Instagram</strong>
            <small>@examdarpan_official</small>
          </span>
          <b aria-hidden="true">→</b>
        </a>

        <a class="ed-social-card ed-x"
           href="https://x.com/exam_darpan"
           target="_blank"
           rel="noopener noreferrer"
           aria-label="Visit Exam Darpan on X">
          <span class="ed-social-logo" aria-hidden="true">
            <svg viewBox="0 0 32 32">
              <path d="M5 4h6.8l5.1 6.8L22.7 4H27l-8.1 9.3L28 28h-6.8l-5.9-7.8L8.6 28H4.3l8.5-9.8L5 4Zm5.1 2.7H8.9l13.9 18.6h1.2L10.1 6.7Z"
                fill="currentColor"/>
            </svg>
          </span>
          <span>
            <strong>X</strong>
            <small>@exam_darpan</small>
          </span>
          <b aria-hidden="true">→</b>
        </a>

      </div>
    `;

    const style = document.createElement('style');
    style.id = 'ed-social-follow-style';

    style.textContent = `
      .ed-social-follow{
        margin-top:14px;
        padding-top:13px;
        border-top:1px solid #e8eef6;
      }

      .ed-social-follow-head{
        display:flex;
        align-items:flex-end;
        justify-content:space-between;
        gap:10px;
        margin-bottom:8px;
      }

      .ed-social-follow-head span{
        color:#0f172a;
        font-size:8px;
        font-weight:950;
        letter-spacing:.13em;
      }

      .ed-social-follow-head small{
        color:#94a3b8;
        font-size:8px;
        font-weight:700;
      }

      .ed-social-grid{
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:8px;
      }

      .ed-social-card{
        min-width:0;
        display:flex;
        align-items:center;
        gap:8px;
        padding:9px;
        border:1px solid #e2e8f0;
        border-radius:14px;
        text-decoration:none;
        color:#0f172a;
        background:#fff;
        transition:
          transform .18s ease,
          box-shadow .18s ease,
          border-color .18s ease;
      }

      .ed-social-card:hover{
        transform:translateY(-2px);
        box-shadow:0 7px 18px rgba(15,23,42,.08);
      }

      .ed-social-logo{
        width:31px;
        height:31px;
        flex:0 0 31px;
        display:grid;
        place-items:center;
        border-radius:10px;
        color:#fff;
      }

      .ed-social-logo svg{
        width:19px;
        height:19px;
      }

      .ed-instagram .ed-social-logo{
        background:linear-gradient(135deg,#f97316,#db2777 55%,#7c3aed);
      }

      .ed-x .ed-social-logo{
        background:#0f172a;
      }

      .ed-social-card span:nth-child(2){
        min-width:0;
        display:flex;
        flex:1;
        flex-direction:column;
        gap:2px;
      }

      .ed-social-card strong{
        font-size:10px;
        line-height:1.15;
        font-weight:950;
      }

      .ed-social-card small{
        overflow:hidden;
        text-overflow:ellipsis;
        white-space:nowrap;
        color:#64748b;
        font-size:7.5px;
        font-weight:700;
      }

      .ed-social-card>b{
        color:#94a3b8;
        font-size:13px;
      }

      @media(max-width:760px){
        .ed-social-follow-head{
          align-items:flex-start;
          flex-direction:column;
          gap:2px;
        }

        .ed-social-grid{
          gap:7px;
        }

        .ed-social-card{
          padding:8px;
        }

        .ed-social-logo{
          width:29px;
          height:29px;
          flex-basis:29px;
        }
      }
    `;

    document.head.appendChild(style);
    community.appendChild(wrap);
  }

  function init() {
    moveDailyQuiz();
    addSocialProfiles();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
