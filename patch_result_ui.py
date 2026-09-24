from pathlib import Path
import re

QUIZ = Path("public/quiz.html")
LB = Path("public/quiz-leaderboard.js")

q = QUIZ.read_text()
l = LB.read_text()

# ---------------------------------------------------------
# 1) Premium result UI CSS — presentation only
# ---------------------------------------------------------
css = r'''
<style id="exam-darpan-result-v4">
/* ===== EXAM DARPAN RESULT EXPERIENCE V4 ===== */

.ed-result-shell{
  overflow:hidden;
  border:1px solid #dbe5f2;
  border-radius:28px;
  background:#fff;
  box-shadow:0 22px 65px rgba(15,35,70,.13);
}

.ed-result-hero{
  position:relative;
  overflow:hidden;
  padding:34px 20px 28px;
  text-align:center;
  background:
    radial-gradient(circle at 50% -15%,rgba(250,204,21,.32),transparent 34%),
    radial-gradient(circle at 0% 20%,rgba(37,99,235,.12),transparent 30%),
    linear-gradient(145deg,#eef5ff,#fff 55%,#ecfdf5);
}

.ed-result-hero:before,
.ed-result-hero:after{
  content:"";
  position:absolute;
  width:120px;
  height:120px;
  border-radius:50%;
  background:rgba(37,99,235,.055);
  top:-65px;
}

.ed-result-hero:before{left:-42px}
.ed-result-hero:after{right:-42px}

.ed-result-emoji{
  position:relative;
  z-index:1;
  font-size:58px;
  line-height:1;
  animation:edResultPop .7s cubic-bezier(.2,.8,.2,1) both;
}

.ed-result-kicker{
  position:relative;
  z-index:1;
  margin-top:10px;
  color:#2453c4;
  font-size:10px;
  font-weight:950;
  letter-spacing:1.7px;
}

.ed-result-hero h2{
  position:relative;
  z-index:1;
  margin:7px 0 5px;
  color:#0f1d36;
  font-size:clamp(25px,5vw,38px);
  font-weight:950;
}

.ed-result-hero p{
  position:relative;
  z-index:1;
  margin:0;
  color:#64748b;
  font-size:13px;
}

.ed-result-score-pill{
  position:relative;
  z-index:1;
  display:inline-flex;
  align-items:center;
  gap:8px;
  margin-top:16px;
  padding:10px 16px;
  border:1px solid #bfdbfe;
  border-radius:999px;
  background:#fff;
  color:#1d4ed8;
  font-size:13px;
  font-weight:950;
  box-shadow:0 8px 24px rgba(37,83,196,.12);
}

.ed-result-summary{
  position:relative;
  z-index:2;
}

.ed-result-flow{
  margin:18px 20px 0;
  padding:11px 13px;
  border:1px solid #e2e8f0;
  border-radius:13px;
  background:#f8fafc;
  color:#64748b;
  text-align:center;
  font-size:11px;
  font-weight:800;
}

.ed-result-flow b{
  color:#2453c4;
}

.ed-result-body{
  padding:18px 22px 26px;
}

.ed-result-body > .ed-review{
  margin-top:26px;
}

.ed-review-heading{
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:10px;
  margin-bottom:12px;
}

.ed-review-heading h3{
  margin:0;
}

.ed-review-subtitle{
  margin-top:3px;
  color:#94a3b8;
  font-size:11px;
}

.ed-review-item{
  transition:transform .15s ease,box-shadow .15s ease;
}

.ed-review-item:hover{
  transform:translateY(-1px);
  box-shadow:0 8px 24px rgba(15,23,42,.06);
}

@keyframes edResultPop{
  0%{
    opacity:0;
    transform:scale(.35) rotate(-12deg);
  }
  70%{
    transform:scale(1.12) rotate(3deg);
  }
  100%{
    opacity:1;
    transform:scale(1) rotate(0);
  }
}

@media(max-width:700px){
  .ed-result-hero{
    padding:28px 14px 23px;
  }

  .ed-result-emoji{
    font-size:50px;
  }

  .ed-result-body{
    padding:15px;
  }

  .ed-result-flow{
    margin:14px 13px 0;
  }
}
</style>
'''

if "exam-darpan-result-v4" not in q:
    q = q.replace("</head>", css + "\n</head>", 1)

# ---------------------------------------------------------
# 2) Replace ONLY the rendered result HTML inside finishQuiz.
#    Calculation/save/event/retry logic remains untouched.
# ---------------------------------------------------------
start = q.find("async function finishQuiz(auto=false){")
if start == -1:
    raise SystemExit("ERROR: finishQuiz not found")

html_start = q.find("box.innerHTML=`", start)
html_end = q.find("`;", html_start)

if html_start == -1 or html_end == -1:
    raise SystemExit("ERROR: result HTML block not found")

new_html = r'''box.innerHTML=`<div class="ed-result-shell">

  <div class="ed-result-hero">
    <div class="ed-result-emoji">${result.accuracy>=90?'🏆':result.accuracy>=70?'🎉':result.accuracy>=50?'🔥':'💪'}</div>

    <div class="ed-result-kicker">
      ${auto?'TIME UP · AUTO SUBMITTED':'TEST SUBMITTED SUCCESSFULLY'}
    </div>

    <h2>
      ${result.accuracy>=90?'Outstanding Attempt!':
        result.accuracy>=70?'Great Job!':
        result.accuracy>=50?'Good Effort!':'Keep Going — Next One Can Be Better!'}
    </h2>

    <p>
      ${esc(quiz.title||'Daily Quiz')}
      · ${result.right}/${result.total} correct
    </p>

    <div class="ed-result-score-pill">
      🎯 ${scoreText} / ${maxText} marks
      · ${result.accuracy}% accuracy
    </div>
  </div>

  <div class="ed-result-summary">
    <div>
      <b>${scoreText}/${maxText}</b>
      <span>Score</span>
    </div>

    <div>
      <b>${result.right}/${result.total}</b>
      <span>Correct</span>
    </div>

    <div>
      <b>${result.wrong}</b>
      <span>Wrong</span>
    </div>

    <div>
      <b>${result.skipped}</b>
      <span>Skipped</span>
    </div>

    <div>
      <b>${result.accuracy}%</b>
      <span>Accuracy</span>
    </div>
  </div>

  <div class="ed-result-flow">
    🎉 <b>Your Result</b>
    &nbsp;→&nbsp;
    🏆 <b>Live Leaderboard</b>
    &nbsp;→&nbsp;
    📖 <b>Answer Review</b>
  </div>

  <div class="ed-result-body">

    ${
      result.negativeMarkingEnabled
      ? `<div class="ed-negative">
          <strong>Negative marking:</strong>
          −${deductText} marks per wrong answer
          (${result.negativeNumerator}/${result.negativeDenominator} of ${result.marksPerQuestion}).
          Total deduction: −${fmtScore(result.wrong*result.negativeDeductionPerWrong)}.
        </div>`
      : `<div class="ed-negative" style="background:#f0fdf4;border-color:#bbf7d0;color:#166534">
          <strong>Negative marking:</strong> OFF — wrong answers have no deduction.
        </div>`
    }

    <p class="meta">
      ⏱️ Time taken: ${fmtTime(result.timeTakenSeconds)}
      ${auto?' · Test auto-submitted':''}
    </p>

    <!-- Existing leaderboard JS will mount HERE.
         Ranking/Firebase/query logic is untouched. -->
    <div id="quizLeaderboardMount"></div>

    <div class="ed-review">

      <div class="ed-review-heading">
        <div>
          <h3>📖 Answer Review</h3>
          <div class="ed-review-subtitle">
            Check your answers and understand every question.
          </div>
        </div>
      </div>

      ${quiz.questions.map((q,i)=>{
        const chosen=answers[i];
        const correct=Number(q.answerIndex);
        const ok=chosen===correct;

        return `
          <div class="ed-review-item ${ok?'ed-review-ok':'ed-review-bad'}">

            <strong>
              ${i+1}. ${esc(q.question)}
            </strong>

            <div class="meta">
              Your answer:
              <b>
                ${chosen===null?'Not answered':esc(q.options[chosen]??'')}
              </b>
            </div>

            <div class="meta">
              Correct answer:
              <b>${esc(q.options[correct]??'')}</b>
            </div>

            ${
              q.explanation
              ? `<div style="margin-top:9px;line-height:1.65">
                   <strong>💡 Explanation:</strong>
                   ${esc(q.explanation)}
                 </div>`
              : ''
            }

          </div>
        `;
      }).join('')}

    </div>

    <div class="result-actions" style="margin-top:18px">
      <button type="button" id="retry" class="btn btn-primary">
        🔄 Try Again
      </button>

      <a class="btn btn-light" href="#previous">
        Previous Quizzes
      </a>
    </div>

  </div>
</div>`;

'''

q = q[:html_start] + new_html + q[html_end+2:]

# ---------------------------------------------------------
# 3) ONLY change leaderboard DOM placement.
#    No ranking, Firebase, query, sorting or score logic.
# ---------------------------------------------------------
old = "if(resultBox) resultBox.appendChild(card);"

new = """if(resultBox){
      const mount=resultBox.querySelector('#quizLeaderboardMount');
      if(mount) mount.replaceChildren(card);
      else resultBox.appendChild(card);
    }"""

if old not in l:
    raise SystemExit("ERROR: leaderboard mount line not found")

l = l.replace(old, new, 1)

QUIZ.write_text(q)
LB.write_text(l)

print("PREMIUM_RESULT_LEADERBOARD_UI_PATCH_OK")
