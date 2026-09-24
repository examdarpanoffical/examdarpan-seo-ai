from pathlib import Path

p = Path("public/quiz.html")
s = p.read_text(encoding="utf-8")

MARKER = '<style id="examdarpan-quiz-ui-v2">'

if MARKER in s:
    print("UI_PATCH_ALREADY_PRESENT")
    raise SystemExit(0)

css = r'''
<style id="examdarpan-quiz-ui-v2">
/* =========================================================
   Exam Darpan Quiz UI v2
   UI ONLY — no quiz/score/timer/leaderboard logic changed
   ========================================================= */

.quiz-shell{
  max-width:1120px!important;
  padding:24px 16px 60px!important;
}

.quiz-shell .card{
  border:1px solid #e2e8f0!important;
  border-radius:22px!important;
  box-shadow:0 14px 45px rgba(15,23,42,.07)!important;
}

/* Quiz header */
.ed-quiz-head{
  position:sticky!important;
  top:10px!important;
  z-index:30!important;
  display:flex!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:16px!important;
  padding:16px 18px!important;
  margin-bottom:12px!important;
  background:rgba(255,255,255,.94)!important;
  backdrop-filter:blur(16px)!important;
  -webkit-backdrop-filter:blur(16px)!important;
  border:1px solid rgba(191,219,254,.85)!important;
  border-radius:20px!important;
  box-shadow:0 12px 35px rgba(15,23,42,.08)!important;
}

.ed-quiz-head strong{
  display:block!important;
  color:#0f172a!important;
  font-size:16px!important;
  font-weight:900!important;
}

.ed-quiz-head .meta{
  margin-top:5px!important;
  color:#64748b!important;
  font-size:11px!important;
}

.ed-timer{
  min-width:108px!important;
  padding:10px 14px!important;
  border-radius:999px!important;
  text-align:center!important;
  background:#eff6ff!important;
  border:1px solid #bfdbfe!important;
  color:#1d4ed8!important;
  font-size:15px!important;
  font-weight:950!important;
  font-variant-numeric:tabular-nums!important;
  box-shadow:0 5px 16px rgba(37,99,235,.10)!important;
}

/* Progress */
.ed-progress{
  height:9px!important;
  margin:10px 2px 14px!important;
  overflow:hidden!important;
  border-radius:999px!important;
  background:#e2e8f0!important;
}

.ed-progress i{
  display:block!important;
  height:100%!important;
  border-radius:999px!important;
  background:linear-gradient(90deg,#2563eb,#06b6d4)!important;
  transition:width .25s ease!important;
}

/* Question number navigation */
.ed-dots{
  display:flex!important;
  gap:7px!important;
  flex-wrap:wrap!important;
  margin:0 0 15px!important;
}

.ed-dot{
  width:35px!important;
  min-width:35px!important;
  height:35px!important;
  padding:0!important;
  border:1px solid #cbd5e1!important;
  border-radius:10px!important;
  background:#fff!important;
  color:#64748b!important;
  font-size:12px!important;
  font-weight:850!important;
  cursor:pointer!important;
  transition:.16s ease!important;
}

.ed-dot:hover{
  transform:translateY(-1px)!important;
  border-color:#93c5fd!important;
}

.ed-dot.done{
  background:#f0fdf4!important;
  border-color:#86efac!important;
  color:#15803d!important;
}

.ed-dot.active{
  background:#2563eb!important;
  border-color:#2563eb!important;
  color:#fff!important;
  box-shadow:0 6px 16px rgba(37,99,235,.22)!important;
}

/* Question card */
.ed-q-card{
  padding:clamp(20px,4vw,32px)!important;
  border:1px solid #e2e8f0!important;
  border-radius:24px!important;
  background:#fff!important;
  box-shadow:0 16px 45px rgba(15,23,42,.07)!important;
}

.ed-q-title{
  margin:0 0 22px!important;
  color:#0f172a!important;
  font-size:clamp(19px,3vw,27px)!important;
  line-height:1.55!important;
  font-weight:900!important;
}

/* Options */
.ed-option{
  display:flex!important;
  align-items:flex-start!important;
  gap:12px!important;
  width:100%!important;
  box-sizing:border-box!important;
  margin:10px 0!important;
  padding:15px 16px!important;
  border:2px solid #e2e8f0!important;
  border-radius:17px!important;
  background:#fff!important;
  color:#0f172a!important;
  cursor:pointer!important;
  transition:
    transform .16s ease,
    border-color .16s ease,
    background .16s ease,
    box-shadow .16s ease!important;
}

.ed-option:hover{
  transform:translateY(-1px)!important;
  border-color:#93c5fd!important;
  box-shadow:0 8px 24px rgba(15,23,42,.06)!important;
}

.ed-option.selected{
  border-color:#2563eb!important;
  background:#eff6ff!important;
  box-shadow:0 8px 24px rgba(37,99,235,.11)!important;
}

.ed-option input{
  margin-top:4px!important;
  accent-color:#2563eb!important;
}

.ed-option span{
  line-height:1.55!important;
}

.ed-option b{
  color:#1d4ed8!important;
}

/* Navigation */
.ed-nav{
  display:flex!important;
  justify-content:space-between!important;
  align-items:center!important;
  gap:10px!important;
  margin-top:22px!important;
  padding-top:17px!important;
  border-top:1px solid #eef2f7!important;
}

.ed-nav .btn{
  min-height:45px!important;
  padding:10px 17px!important;
  border-radius:13px!important;
  font-weight:850!important;
}

.ed-submit-note{
  margin-top:10px!important;
  padding:10px 12px!important;
  border-radius:11px!important;
  background:#f8fafc!important;
  color:#64748b!important;
  font-size:11px!important;
  text-align:center!important;
}

/* Result */
.ed-result-summary{
  display:grid!important;
  grid-template-columns:repeat(5,minmax(0,1fr))!important;
  gap:10px!important;
  margin:18px 0!important;
}

.ed-result-summary>div{
  padding:15px 8px!important;
  border:1px solid #e2e8f0!important;
  border-radius:15px!important;
  background:#f8fafc!important;
  text-align:center!important;
}

.ed-result-summary b{
  display:block!important;
  color:#0f172a!important;
  font-size:21px!important;
  font-weight:950!important;
}

.ed-result-summary span{
  display:block!important;
  margin-top:3px!important;
  color:#64748b!important;
  font-size:10px!important;
  font-weight:750!important;
}

.ed-negative{
  padding:13px 15px!important;
  border-radius:14px!important;
  border:1px solid #fed7aa!important;
  background:#fff7ed!important;
  color:#9a3412!important;
  font-size:12px!important;
}

.ed-review{
  margin-top:22px!important;
}

.ed-review>h3{
  color:#0f172a!important;
}

.ed-review-item{
  padding:16px!important;
  margin:10px 0!important;
  border:1px solid #e2e8f0!important;
  border-radius:16px!important;
  background:#fff!important;
}

.ed-review-ok{
  border-left:4px solid #16a34a!important;
  background:#f0fdf4!important;
}

.ed-review-bad{
  border-left:4px solid #dc2626!important;
  background:#fef2f2!important;
}

.result-actions{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:10px!important;
}

.result-actions .btn{
  min-height:45px!important;
  border-radius:13px!important;
  font-weight:850!important;
}

/* Mobile */
@media(max-width:700px){
  .quiz-shell{
    padding:14px 10px 40px!important;
  }

  .ed-quiz-head{
    top:5px!important;
    padding:12px!important;
    border-radius:16px!important;
  }

  .ed-quiz-head strong{
    font-size:14px!important;
  }

  .ed-timer{
    min-width:82px!important;
    padding:8px 9px!important;
    font-size:13px!important;
  }

  .ed-q-card{
    padding:18px 14px!important;
    border-radius:19px!important;
  }

  .ed-q-title{
    font-size:18px!important;
  }

  .ed-option{
    padding:13px!important;
    border-radius:14px!important;
  }

  .ed-nav{
    position:sticky!important;
    bottom:7px!important;
    z-index:20!important;
    padding:10px!important;
    border:1px solid #e2e8f0!important;
    border-radius:15px!important;
    background:rgba(255,255,255,.94)!important;
    backdrop-filter:blur(12px)!important;
  }

  .ed-result-summary{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }

  .ed-result-summary>div:first-child{
    grid-column:1/-1!important;
  }
}

@media(max-width:420px){
  .ed-dots{
    overflow-x:auto!important;
    flex-wrap:nowrap!important;
    padding-bottom:3px!important;
  }

  .ed-dot{
    flex:0 0 35px!important;
  }
}
</style>
'''

head = s.find("</head>")
if head == -1:
    raise SystemExit("ERROR: </head> not found")

s = s[:head] + css + "\n" + s[head:]
p.write_text(s, encoding="utf-8")

print("PATCH_OK")
