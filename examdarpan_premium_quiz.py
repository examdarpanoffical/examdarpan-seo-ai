from pathlib import Path

p = Path("public/quiz.html")
s = p.read_text(encoding="utf-8")

marker = "exam-darpan-premium-quiz-v3"

if marker in s:
    print("PATCH_ALREADY_APPLIED")
    raise SystemExit(0)

css = r"""
<style id="exam-darpan-premium-quiz-v3">

/* ===== EXAM DARPAN PREMIUM QUIZ UI ===== */

body{
  background:
    radial-gradient(circle at 8% 0%,rgba(37,83,196,.08),transparent 28%),
    radial-gradient(circle at 95% 5%,rgba(79,70,216,.08),transparent 25%),
    #f4f7fc !important;
}

.ed-quiz-head{
  position:sticky!important;
  top:6px!important;
  z-index:50!important;
  display:flex!important;
  justify-content:space-between!important;
  align-items:center!important;
  gap:15px!important;
  padding:15px 17px!important;
  margin-bottom:12px!important;
  border:1px solid #d8e3f3!important;
  border-radius:21px!important;
  background:rgba(255,255,255,.94)!important;
  backdrop-filter:blur(16px)!important;
  -webkit-backdrop-filter:blur(16px)!important;
  box-shadow:0 12px 38px rgba(15,35,70,.09)!important;
}

.ed-quiz-title{
  color:#101d38!important;
  font-size:16px!important;
  font-weight:950!important;
}

.ed-question-meta{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:7px!important;
  margin-top:5px!important;
  color:#718096!important;
  font-size:11px!important;
}

.ed-q-chip{
  padding:4px 9px!important;
  border-radius:999px!important;
  background:#eef4ff!important;
  color:#2453c4!important;
  font-weight:900!important;
}

.ed-timer-wrap{
  min-width:120px!important;
  text-align:center!important;
}

.ed-timer{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-width:105px!important;
  padding:10px 14px!important;
  border:1px solid #cbdcfb!important;
  border-radius:999px!important;
  background:linear-gradient(135deg,#eff6ff,#f8faff)!important;
  color:#2453c4!important;
  font-size:15px!important;
  font-weight:950!important;
  font-variant-numeric:tabular-nums!important;
  box-shadow:0 7px 20px rgba(37,83,196,.10)!important;
}

.ed-timer.danger{
  background:#fff1f2!important;
  border-color:#fecdd3!important;
  color:#be123c!important;
  animation:edPulse 1s infinite!important;
}

.ed-timer-label{
  display:block!important;
  margin-top:4px!important;
  color:#7a8799!important;
  font-size:9px!important;
  font-weight:900!important;
  letter-spacing:.08em!important;
}

@keyframes edPulse{
  50%{transform:scale(1.04)}
}

.ed-progress-wrap{
  display:flex!important;
  align-items:center!important;
  gap:9px!important;
  margin:10px 0 14px!important;
}

.ed-progress{
  flex:1!important;
  height:9px!important;
  overflow:hidden!important;
  border-radius:999px!important;
  background:#dfe6f0!important;
}

.ed-progress i{
  display:block!important;
  height:100%!important;
  border-radius:999px!important;
  background:linear-gradient(90deg,#2453c4,#4f46d8,#06b6d4)!important;
  transition:width .3s ease!important;
}

.ed-progress-text{
  color:#66748a!important;
  font-size:10px!important;
  font-weight:900!important;
}

.ed-dots{
  display:flex!important;
  gap:6px!important;
  flex-wrap:wrap!important;
  margin:0 0 15px!important;
}

.ed-dot{
  width:34px!important;
  min-width:34px!important;
  height:34px!important;
  padding:0!important;
  border:1px solid #cbd5e1!important;
  border-radius:10px!important;
  background:#fff!important;
  color:#64748b!important;
  font-size:11px!important;
  font-weight:900!important;
  cursor:pointer!important;
  transition:.16s ease!important;
}

.ed-dot:hover{
  transform:translateY(-1px)!important;
  border-color:#8fb3ed!important;
}

.ed-dot.done{
  border-color:#86efac!important;
  background:#f0fdf4!important;
  color:#15803d!important;
}

.ed-dot.active{
  border-color:#2453c4!important;
  background:linear-gradient(135deg,#2453c4,#4f46d8)!important;
  color:#fff!important;
  box-shadow:0 7px 18px rgba(37,83,196,.23)!important;
}

.ed-q-card{
  position:relative!important;
  overflow:hidden!important;
  padding:clamp(20px,4vw,34px)!important;
  border:1px solid #e0e7f0!important;
  border-radius:25px!important;
  background:#fff!important;
  box-shadow:0 18px 48px rgba(20,40,75,.075)!important;
}

.ed-q-card:before{
  content:""!important;
  position:absolute!important;
  left:0!important;
  top:0!important;
  bottom:0!important;
  width:4px!important;
  background:linear-gradient(180deg,#2453c4,#06b6d4)!important;
}

.ed-q-number{
  display:inline-flex!important;
  padding:6px 10px!important;
  border-radius:999px!important;
  background:#eef4ff!important;
  color:#2453c4!important;
  font-size:11px!important;
  font-weight:950!important;
}

.ed-q-title{
  margin:12px 0 23px!important;
  color:#111d35!important;
  font-size:clamp(19px,3vw,27px)!important;
  line-height:1.58!important;
  font-weight:900!important;
}

.ed-option{
  display:flex!important;
  align-items:flex-start!important;
  gap:12px!important;
  width:100%!important;
  box-sizing:border-box!important;
  margin:10px 0!important;
  padding:15px 16px!important;
  border:2px solid #e3e8f0!important;
  border-radius:17px!important;
  background:#fff!important;
  color:#17233b!important;
  cursor:pointer!important;
  transition:.16s ease!important;
}

.ed-option:hover{
  transform:translateY(-1px)!important;
  border-color:#91b5ef!important;
  box-shadow:0 9px 26px rgba(16,37,72,.065)!important;
}

.ed-option.selected{
  border-color:#3b63c8!important;
  background:linear-gradient(135deg,#f0f5ff,#f8f8ff)!important;
  box-shadow:0 9px 26px rgba(37,83,196,.11)!important;
}

.ed-option input{
  margin-top:4px!important;
  accent-color:#2453c4!important;
}

.ed-option b{
  color:#2453c4!important;
  font-weight:950!important;
}

.ed-nav{
  display:flex!important;
  justify-content:space-between!important;
  gap:10px!important;
  margin-top:22px!important;
  padding-top:17px!important;
  border-top:1px solid #edf1f6!important;
}

.ed-nav .btn{
  min-height:46px!important;
  padding:10px 18px!important;
  border-radius:13px!important;
  font-weight:900!important;
}

.ed-nav .btn-primary{
  border:0!important;
  background:linear-gradient(135deg,#2453c4,#4f46d8)!important;
  box-shadow:0 8px 20px rgba(37,83,196,.20)!important;
}

.ed-submit-note{
  margin-top:10px!important;
  padding:11px!important;
  border-radius:12px!important;
  background:#f8fafc!important;
  color:#718096!important;
  font-size:11px!important;
  text-align:center!important;
}

/* ===== RESULT / CELEBRATION ===== */

.ed-result{
  overflow:hidden!important;
  border:1px solid #dce5f2!important;
  border-radius:28px!important;
  background:#fff!important;
  box-shadow:0 22px 65px rgba(20,40,75,.12)!important;
}

.ed-result-hero{
  position:relative!important;
  padding:34px 22px 27px!important;
  text-align:center!important;
  background:
    radial-gradient(circle at 50% -10%,rgba(251,191,36,.22),transparent 30%),
    linear-gradient(145deg,#eef5ff,#fff 55%,#ecfdf5)!important;
}

.ed-celebrate{
  font-size:45px!important;
  line-height:1!important;
  margin-bottom:10px!important;
  animation:edCelebrate .8s ease both!important;
}

@keyframes edCelebrate{
  0%{transform:scale(.5) rotate(-8deg);opacity:0}
  70%{transform:scale(1.12) rotate(2deg)}
  100%{transform:scale(1);opacity:1}
}

.ed-result-kicker{
  color:#2453c4!important;
  font-size:10px!important;
  font-weight:950!important;
  letter-spacing:1.5px!important;
}

.ed-result-hero h2{
  margin:8px 0 6px!important;
  color:#101d38!important;
  font-size:clamp(25px,4vw,36px)!important;
  font-weight:950!important;
}

.ed-result-sub{
  margin:0!important;
  color:#718096!important;
  font-size:13px!important;
}

.ed-result-summary{
  display:grid!important;
  grid-template-columns:repeat(5,minmax(0,1fr))!important;
  gap:10px!important;
  padding:20px 22px 0!important;
}

.ed-result-summary>div{
  padding:16px 8px!important;
  border:1px solid #e1e7f0!important;
  border-radius:16px!important;
  background:linear-gradient(145deg,#fff,#f8fafc)!important;
  text-align:center!important;
}

.ed-result-summary>div:first-child{
  border-color:#cbd9f4!important;
  background:linear-gradient(145deg,#eef4ff,#f7f5ff)!important;
}

.ed-result-summary b{
  display:block!important;
  color:#13213b!important;
  font-size:22px!important;
  font-weight:950!important;
}

.ed-result-summary span{
  display:block!important;
  margin-top:4px!important;
  color:#718096!important;
  font-size:10px!important;
  font-weight:800!important;
}

.ed-result-body{
  padding:20px 22px 25px!important;
}

.ed-negative{
  padding:13px 15px!important;
  border:1px solid #fed7aa!important;
  border-radius:14px!important;
  background:#fff7ed!important;
  color:#9a3412!important;
  font-size:12px!important;
}

.ed-result-statline{
  margin:14px 0!important;
  padding:12px!important;
  border-radius:13px!important;
  background:#f8fafc!important;
  color:#66748a!important;
  font-size:12px!important;
  text-align:center!important;
}

.ed-review{
  margin-top:24px!important;
}

.ed-review-heading h3{
  margin:0 0 13px!important;
  color:#101d38!important;
  font-size:20px!important;
  font-weight:950!important;
}

.ed-review-item{
  padding:17px!important;
  margin:10px 0!important;
  border:1px solid #e1e7ef!important;
  border-radius:16px!important;
  background:#fff!important;
  box-shadow:0 5px 18px rgba(20,40,75,.035)!important;
}

.ed-review-ok{
  border-left:5px solid #16a34a!important;
  background:#f2fcf5!important;
}

.ed-review-bad{
  border-left:5px solid #dc2626!important;
  background:#fff6f6!important;
}

.ed-actions{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:10px!important;
  margin-top:20px!important;
}

.ed-actions .btn{
  min-height:46px!important;
  border-radius:13px!important;
  font-weight:900!important;
}

/* ===== MOBILE ===== */

@media(max-width:700px){

  .ed-quiz-head{
    top:4px!important;
    padding:11px!important;
    border-radius:16px!important;
  }

  .ed-quiz-title{
    font-size:13px!important;
  }

  .ed-timer-wrap{
    min-width:90px!important;
  }

  .ed-timer{
    min-width:78px!important;
    padding:8px 9px!important;
    font-size:13px!important;
  }

  .ed-dots{
    flex-wrap:nowrap!important;
    overflow-x:auto!important;
    padding-bottom:4px!important;
    scrollbar-width:none!important;
  }

  .ed-dots::-webkit-scrollbar{
    display:none!important;
  }

  .ed-dot{
    flex:0 0 33px!important;
  }

  .ed-q-card{
    padding:19px 14px!important;
    border-radius:20px!important;
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
    z-index:35!important;
    padding:9px!important;
    border:1px solid #e0e6ef!important;
    border-radius:15px!important;
    background:rgba(255,255,255,.94)!important;
    backdrop-filter:blur(12px)!important;
  }

  .ed-result-summary{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    padding-left:14px!important;
    padding-right:14px!important;
  }

  .ed-result-summary>div:first-child{
    grid-column:1/-1!important;
  }

  .ed-result-body{
    padding:15px!important;
  }
}

</style>
"""

pos = s.rfind("</head>")

if pos == -1:
    raise SystemExit("ERROR: </head> not found")

s = s[:pos] + css + "\n" + s[pos:]

p.write_text(s, encoding="utf-8")

print("PREMIUM_UI_PATCH_OK")
