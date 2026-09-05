import hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import firebase_admin
from firebase_admin import credentials, firestore
from google import genai
from google.genai import types

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SOURCES_FILE = os.path.join(BASE, "sources.json")
UA = os.getenv("MONITOR_USER_AGENT", "ExamDarpanOfficialMonitor/1.0 (+https://examdarpan.in)")
MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "3"))
MAX_TEXT_CHARS = int(os.getenv("MAX_SOURCE_CHARS", "30000"))
BOOTSTRAP_SKIP_EXISTING = os.getenv("BOOTSTRAP_SKIP_EXISTING", "false").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

KEYWORDS_GLOBAL = ["recruit", "result", "admit", "answer", "key", "syllabus", "notification", "advertisement", "press", "exam", "परीक्षा", "भर्ती", "विज्ञप्ति", "परिणाम", "प्रवेश", "उत्तर कुंजी", "परीक्षा तिथि", "आवेदन", "आदेश", "परिपत्र"]


def log(*args):
    print(datetime.now().isoformat(), *args, flush=True)


def get_db():
    if not firebase_admin._apps:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON secret is missing")
        cred = credentials.Certificate(json.loads(raw))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for x in soup(["script", "style", "noscript", "svg"]):
        x.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return re.sub(r"\n{3,}", "\n\n", text)


def fetch(url):
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "hi,en;q=0.8"}, timeout=35)
    r.raise_for_status()
    return r


def extract_pdf(url, data):
    path = os.path.join("/tmp", "source.pdf")
    with open(path, "wb") as f:
        f.write(data)
    reader = PdfReader(path)
    parts = []
    for page in reader.pages[:25]:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            pass
    return "\n".join(parts).strip()


def is_candidate(title, href, source):
    hay = (title + " " + href).lower()
    return any(k.lower() in hay for k in source["keywords"] + KEYWORDS_GLOBAL)


def discover(source):
    r = fetch(source["url"])
    content_type = r.headers.get("content-type", "").lower()
    if "pdf" in content_type or source["url"].lower().endswith(".pdf"):
        return [{"title": source["name"], "url": source["url"], "source_page": source["url"]}]
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    seen = set()
    base_host = urlparse(source["url"]).netloc
    for a in soup.find_all("a", href=True):
        title = " ".join(a.get_text(" ", strip=True).split())
        href = urljoin(source["url"], a["href"].strip())
        if not title or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        if urlparse(href).netloc and urlparse(href).netloc != base_host:
            continue
        if href in seen or not is_candidate(title, href, source):
            continue
        seen.add(href)
        items.append({"title": title[:300], "url": href, "source_page": source["url"]})
    return items[:40]


def fetch_source_text(item):
    r = fetch(item["url"])
    ctype = r.headers.get("content-type", "").lower()
    if "pdf" in ctype or item["url"].lower().split("?")[0].endswith(".pdf"):
        return extract_pdf(item["url"], r.content)
    return clean_text(r.text)


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:110] or hashlib.sha1(text.encode()).hexdigest()[:12]


def generate_article(topic, source_text, source_url, source_name):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY secret is missing")
    client = genai.Client(api_key=api_key)
    prompt = f"""You are the senior Hindi editorial assistant for Exam Darpan, an independent Indian education and government-job information portal.

Write a publication-quality Hindi draft using ONLY the official source text below.

STRICT FACT RULES:
- The official source is the factual authority.
- Never invent or guess dates, vacancies, fees, age limits, eligibility, salary, selection process, exam dates, URLs, post names or department claims.
- If a fact is absent, omit it.
- Preserve exact numbers and dates.
- Clearly label tentative/proposed dates as tentative/proposed.
- Do not call Exam Darpan an official government website.
- Do not claim that an application link exists unless the source provides it.

STYLE:
- Natural Hindi for Indian students/job seekers.
- Useful headings and short paragraphs.
- Use a table only when it improves clarity.
- No clickbait or filler.

OUTPUT:
Return HTML only using h2,h3,p,ul,ol,li,strong,table,thead,tbody,tr,th,td,a.
Start exactly with: <p>AI-assisted draft — Human verification required before publication.</p>
End with a concise official-source verification note.

TOPIC: {topic}
OFFICIAL SOURCE: {source_name}
OFFICIAL SOURCE URL: {source_url}

SOURCE TEXT:
{source_text[:MAX_TEXT_CHARS]}
"""
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.2))
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text


def main():
    db = get_db()
    posts = db.collection("posts")
    seen = db.collection("monitor_seen")
    sources = json.load(open(SOURCES_FILE, encoding="utf-8"))
    total_new = 0

    for source in sorted(sources, key=lambda x: x.get("priority", 9)):
        log("Checking", source["name"])
        try:
            discovered = discover(source)
        except Exception as e:
            log("SOURCE ERROR", source["id"], repr(e))
            continue
        for item in discovered[:MAX_ITEMS_PER_SOURCE]:
            key = hashlib.sha256((source["id"] + "|" + item["url"]).encode()).hexdigest()
            ref = seen.document(key)
            if ref.get().exists:
                continue
            # Mark first so a repeated failed run doesn't spam. Failed items remain visible in state for diagnosis.
            ref.set({"sourceId": source["id"], "sourceName": source["name"], "url": item["url"], "title": item["title"], "checkedAt": firestore.SERVER_TIMESTAMP, "status": "seen"})
            if BOOTSTRAP_SKIP_EXISTING:
                continue
            try:
                text = fetch_source_text(item)
                if len(text.strip()) < 120:
                    log("SKIP short source", item["url"])
                    ref.update({"status": "skipped_short"})
                    continue
                article = generate_article(item["title"], text, item["url"], source["name"])
                data = {
                    "title": item["title"],
                    "slug": slugify(item["title"]),
                    "category": "Rajasthan Jobs" if source["id"] in {"rssb", "rpsc", "rajasthan-recruitment", "rajasthan-police"} else "Latest Updates",
                    "excerpt": "",
                    "content": article,
                    "featuredImage": "",
                    "officialNotificationUrl": item["url"],
                    "applyOnlineUrl": "",
                    "officialWebsiteUrl": source["url"],
                    "notificationPdfUrl": item["url"] if item["url"].lower().split("?")[0].endswith(".pdf") else "",
                    "tags": ["Rajasthan", source["id"], "Latest Update"],
                    "authorName": "Exam Darpan AI",
                    "authorUrl": "https://examdarpan.in/author.html",
                    "status": "draft",
                    "sourceName": source["name"],
                    "sourceUrl": item["url"],
                    "autoGenerated": True,
                    "updatedAt": firestore.SERVER_TIMESTAMP,
                    "createdAt": firestore.SERVER_TIMESTAMP,
                }
                doc = posts.add(data)[1]
                ref.update({"status": "draft_created", "postId": doc.id})
                total_new += 1
                log("DRAFT CREATED", doc.id, item["title"])
            except Exception as e:
                log("ITEM ERROR", item["url"], repr(e))
                ref.update({"status": "error", "error": str(e)[:1000]})
    log("Done. New drafts:", total_new)


if __name__ == "__main__":
    main()
