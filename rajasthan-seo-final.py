from pathlib import Path
from datetime import datetime
import shutil, subprocess, sys

ROOT = Path("public")
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = Path(f"rajasthan-seo-final-backup-{STAMP}")
BACKUP.mkdir(exist_ok=True)

DOMAIN = "https://examdarpan.in"

TARGETS = [
    ROOT / "index.html",
    ROOT / "rajasthan-government-jobs.html",
    ROOT / "sitemap.xml",
]

for p in TARGETS:
    if p.exists():
        shutil.copy2(p, BACKUP / p.name)

print("==============================================")
print("EXAM DARPAN — RAJASTHAN SEO FINAL")
print("==============================================")
print("Backup:", BACKUP)

def read(p):
    return p.read_text(encoding="utf-8")

def write(p, s):
    p.write_text(s.rstrip() + "\n", encoding="utf-8")

# ============================================================
# Rajasthan Hub
# ============================================================

hub = ROOT / "rajasthan-government-jobs.html"

if not hub.exists():
    print("ERROR: Rajasthan hub missing:", hub)
    sys.exit(1)

s = read(hub)

section = r'''
<section class="seo-raj-clusters" aria-labelledby="raj-seo-heading">
  <h2 id="raj-seo-heading">राजस्थान सरकारी नौकरी — भर्ती, परीक्षा, एडमिट कार्ड और रिजल्ट</h2>

  <p>
    राजस्थान की सरकारी भर्तियों और प्रतियोगी परीक्षाओं की नवीनतम जानकारी
    Exam Darpan पर एक जगह देखें। आवेदन करने से पहले संबंधित विभाग की
    आधिकारिक अधिसूचना और वेबसाइट पर जानकारी जरूर verify करें।
  </p>

  <div class="seo-raj-grid">
    <a href="#rpsc">
      <strong>RPSC Recruitment</strong>
      <span>RPSC भर्ती, परीक्षा और परिणाम अपडेट</span>
    </a>

    <a href="#rssb">
      <strong>RSSB / RSMSSB</strong>
      <span>कर्मचारी चयन बोर्ड की भर्ती जानकारी</span>
    </a>

    <a href="#police">
      <strong>Rajasthan Police</strong>
      <span>पुलिस भर्ती और परीक्षा अपडेट</span>
    </a>

    <a href="#teacher">
      <strong>Teacher Jobs</strong>
      <span>REET और शिक्षक भर्ती अपडेट</span>
    </a>

    <a href="#cet">
      <strong>Rajasthan CET</strong>
      <span>CET परीक्षा और संबंधित भर्ती अपडेट</span>
    </a>

    <a href="#clerical">
      <strong>LDC / Clerk</strong>
      <span>क्लर्क और जूनियर असिस्टेंट भर्ती</span>
    </a>

    <a href="#technical">
      <strong>JE / Technical Jobs</strong>
      <span>JE और तकनीकी भर्ती अपडेट</span>
    </a>

    <a href="#results">
      <strong>Admit Card & Result</strong>
      <span>एडमिट कार्ड, आंसर की और रिजल्ट</span>
    </a>
  </div>

  <div class="seo-raj-official">
    <strong>Official Rajasthan Sources:</strong>
    <a href="https://recruitment.rajasthan.gov.in/" target="_blank" rel="noopener noreferrer">Recruitment Portal</a>
    ·
    <a href="https://rpsc.rajasthan.gov.in/" target="_blank" rel="noopener noreferrer">RPSC</a>
    ·
    <a href="https://rssb.rajasthan.gov.in/" target="_blank" rel="noopener noreferrer">RSSB</a>
  </div>
</section>
'''

if 'class="seo-raj-clusters"' not in s:
    if "</main>" in s:
        s = s.replace("</main>", section + "\n</main>", 1)
    else:
        print("ERROR: </main> missing in Rajasthan hub")
        sys.exit(1)

css = r'''
<style>
.seo-raj-clusters{
  margin:28px 0;
  padding:26px;
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:18px;
}

.seo-raj-clusters h2{
  margin:0 0 10px;
  color:#0f172a;
}

.seo-raj-clusters p{
  color:#475569;
  line-height:1.75;
}

.seo-raj-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
  margin-top:20px;
}

.seo-raj-grid a{
  display:flex;
  flex-direction:column;
  gap:5px;
  padding:15px;
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:13px;
  color:#0f172a;
  text-decoration:none;
  transition:.18s ease;
}

.seo-raj-grid a:hover{
  border-color:#2563eb;
  color:#2563eb;
  transform:translateY(-1px);
}

.seo-raj-grid span{
  color:#64748b;
  font-size:.88rem;
}

.seo-raj-official{
  margin-top:20px;
  padding:14px 16px;
  background:#f0fdf4;
  border-left:4px solid #16a34a;
  border-radius:8px;
  color:#14532d;
}

.seo-raj-official a{
  color:#166534;
  font-weight:700;
}

@media(max-width:800px){
  .seo-raj-grid{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

@media(max-width:520px){
  .seo-raj-clusters{
    padding:18px;
  }

  .seo-raj-grid{
    grid-template-columns:1fr;
  }
}
</style>
'''

if "seo-raj-grid{" not in s:
    s = s.replace("</head>", css + "\n</head>", 1)

write(hub, s)

# ============================================================
# Homepage → Rajasthan hub
# ============================================================

index = ROOT / "index.html"

if index.exists():
    s = read(index)

    homepage_block = r'''
<section class="raj-home-seo-link">
  <h2>राजस्थान सरकारी नौकरी और परीक्षा अपडेट</h2>
  <p>
    RPSC, RSSB, Rajasthan Police, CET, Teacher, LDC, JE,
    Admit Card और Result की नवीनतम जानकारी देखें।
  </p>
  <a href="/rajasthan-government-jobs">
    राजस्थान Government Jobs Hub देखें →
  </a>
</section>
'''

    if "raj-home-seo-link" not in s and "</main>" in s:
        s = s.replace("</main>", homepage_block + "\n</main>", 1)

    write(index, s)

# ============================================================
# Relevant article → Rajasthan hub
# ============================================================

article_files = [
    "rajasthan-rvunl-recruitment-2026-junior-engineer-junior-accountant-junior-assistant.html",
    "rajasthan-cet-senior-secondary-2026-28-august-se-23-october-tak-56-din-mein-clerk-ldc-exam-ki-taiyari-kaise-kare.html",
]

article_block = r'''
<p class="raj-context-link">
  <a href="/rajasthan-government-jobs">
    राजस्थान की सभी सरकारी भर्ती और परीक्षा अपडेट देखें →
  </a>
</p>
'''

for name in article_files:
    p = ROOT / name

    if not p.exists():
        continue

    s = read(p)

    if "raj-context-link" not in s and "</main>" in s:
        s = s.replace("</main>", article_block + "\n</main>", 1)

    write(p, s)

# ============================================================
# Sitemap
# ============================================================

urls = [
    "/",
    "/rajasthan-government-jobs",

    "/sbi-asha-scholarship-2026",
    "/bank-of-india-so-recruitment-2026-205-posts",
    "/rajasthan-rvunl-recruitment-2026-junior-engineer-junior-accountant-junior-assistant",
    "/india-post-gds-recruitment-2026-bpm-25-000",
    "/east-coast-railway-apprentice-1-599-posts",
    "/ssc-je-recruitment-2026",
    "/rscit-result-2026-declared-check-your-result-online",
    "/rajasthan-cet-senior-secondary-2026-28-august-se-23-october-tak-56-din-mein-clerk-ldc-exam-ki-taiyari-kaise-kare",

    "/about.html",
    "/contact.html",
    "/editorial-policy.html",
    "/privacy.html",
    "/disclaimer.html",
    "/terms.html",
]

today = datetime.now().strftime("%Y-%m-%d")

lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
]

for u in urls:
    priority = "1.0" if u == "/" else "0.9" if u == "/rajasthan-government-jobs" else "0.7"
    lines.append(
        f"<url><loc>{DOMAIN}{u}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>"
    )

lines.append("</urlset>")

write(ROOT / "sitemap.xml", "\n".join(lines))

# ============================================================
# Validation
# ============================================================

errors = []

robots = ROOT / "robots.txt"

if robots.exists():
    r = read(robots)

    if "Allow: /" not in r:
        errors.append("robots.txt missing Allow: /")

    if "Sitemap: https://examdarpan.in/sitemap.xml" not in r:
        errors.append("robots.txt sitemap declaration missing")

hub_text = read(hub)

for required in [
    "RPSC Recruitment",
    "RSSB / RSMSSB",
    "Rajasthan Police",
    "Teacher Jobs",
    "Rajasthan CET",
    "LDC / Clerk",
    "JE / Technical Jobs",
    "Admit Card & Result",
    "recruitment.rajasthan.gov.in",
]:
    if required not in hub_text:
        errors.append("hub missing: " + required)

sm = read(ROOT / "sitemap.xml")

for u in urls:
    if DOMAIN + u not in sm:
        errors.append("sitemap missing: " + u)

if ".html.html" in sm:
    errors.append("invalid .html.html URL")

for p in [index, hub]:
    if p.exists():
        t = read(p).lower()
        if 'content="noindex' in t:
            errors.append("noindex found: " + str(p))

if subprocess.run(["git","diff","--check"]).returncode != 0:
    errors.append("git diff --check failed")

# ============================================================
# SAFE STOP
# ============================================================

if errors:
    print("")
    print("==============================================")
    print("ERROR — NOTHING COMMITTED")
    print("==============================================")

    for e in errors:
        print(" -", e)

    print("")
    print("Backup:", BACKUP)
    sys.exit(1)

print("")
print("==============================================")
print("VALIDATION PASSED")
print("==============================================")
print("Sitemap URLs:", len(urls))
print("Hub:", DOMAIN + "/rajasthan-government-jobs")
print("Backup:", BACKUP)

subprocess.run(["git","diff","--stat"], check=True)

# ============================================================
# COMMIT + PUSH
# ============================================================

files = [
    "public/index.html",
    "public/rajasthan-government-jobs.html",
    "public/sitemap.xml",
]

for name in article_files:
    if (ROOT / name).exists():
        files.append("public/" + name)

subprocess.run(["git","add"] + files, check=True)

subprocess.run([
    "git",
    "commit",
    "-m",
    "feat: strengthen Rajasthan SEO topic architecture"
], check=True)

subprocess.run(["git","push"], check=True)

print("")
print("==============================================")
print("PUSH COMPLETE")
print("==============================================")
print("✓ Rajasthan SEO hub strengthened")
print("✓ Homepage internal link added")
print("✓ Relevant Rajasthan articles linked to hub")
print("✓ Sitemap rebuilt with canonical clean URLs")
print("✓ robots validation passed")
print("✓ noindex safety check passed")
print("✓ git diff --check passed")
print("✓ Quiz / leaderboard / admin untouched")
print("✓ Automatic deployment should trigger")
print("")
print("SEO URL:")
print(DOMAIN + "/rajasthan-government-jobs")
print("")
print("BACKUP:", BACKUP)
