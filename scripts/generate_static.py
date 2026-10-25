import os
import re
import json
import html
import urllib.request
import urllib.error
from datetime import datetime, timezone

SITE_DOMAIN = "https://examdarpan.in"
PROJECT_ID = "examdarpan-seo-ai"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "public")
ARTICLE_DIR = os.path.join(OUTPUT_DIR, "article")

def format_w3c_date(dt=None):
    if not dt:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(dt, (int, float)):
        if dt > 1e11:
            dt = dt / 1000.0
        return datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(dt, str):
        clean_str = dt.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(clean_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            try:
                return datetime.strptime(clean_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def clean_slug(slug):
    slug = str(slug or "").strip().lower()
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    return re.sub(r'-+', '-', slug).strip('-')

def fetch_posts_via_rest():
    """Fetch posts directly from Firestore REST API without needing service account keys"""
    posts = []
    collections = ["posts", "articles"]
    for col in collections:
        url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{col}?pageSize=100"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ExamDarpan-Builder/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                docs = data.get("documents", [])
                print(f"REST API: Found {len(docs)} items in '{col}'")
                for doc in docs:
                    fields = doc.get("fields", {})
                    # Parse Firestore REST fields format
                    post = {}
                    for k, v in fields.items():
                        if "stringValue" in v:
                            post[k] = v["stringValue"]
                        elif "timestampValue" in v:
                            post[k] = v["timestampValue"]
                        elif "integerValue" in v:
                            post[k] = int(v["integerValue"])
                        elif "booleanValue" in v:
                            post[k] = v["booleanValue"]
                    doc_id = doc.get("name", "").split("/")[-1]
                    if not post.get("slug"):
                        post["slug"] = doc_id
                    posts.append(post)
                if posts:
                    break
        except Exception as e:
            print(f"REST fetch for '{col}' skipped: {e}")
    return posts

def fetch_posts_via_admin():
    """Attempt fetch using firebase-admin if service account credentials exist"""
    cred_json_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if not cred_json_str or not cred_json_str.startswith("{"):
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(cred_json_str))
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        posts = []
        for col in ["posts", "articles"]:
            docs = list(db.collection(col).stream())
            if docs:
                for d in docs:
                    data = d.to_dict()
                    if not data.get("slug"):
                        data["slug"] = d.id
                    posts.append(data)
                break
        return posts
    except Exception as e:
        print(f"Admin SDK skipped: {e}")
        return None

def build_article_html(post):
    title = html.escape(str(post.get("title") or "Exam Notification"))
    raw_desc = post.get("summary") or post.get("metaDescription") or post.get("title") or ""
    description = html.escape(str(raw_desc)[:160])
    slug = clean_slug(post.get("slug"))
    content = post.get("content") or post.get("body") or "<p>Notification details loading...</p>"
    category = html.escape(str(post.get("category") or "Recruitment"))
    
    canonical_url = f"{SITE_DOMAIN}/article/{slug}"
    created_at = format_w3c_date(post.get("createdAt"))
    updated_at = format_w3c_date(post.get("updatedAt") or post.get("createdAt"))

    schema_data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": post.get("title") or "Exam Darpan Update",
        "datePublished": created_at,
        "dateModified": updated_at,
        "mainEntityOfPage": canonical_url,
        "publisher": {
            "@type": "Organization",
            "name": "Exam Darpan",
            "logo": {
                "@type": "ImageObject",
                "url": f"{SITE_DOMAIN}/assets/logo.png"
            }
        }
    }

    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Exam Darpan</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical_url}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <meta property="og:locale" content="hi_IN">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:site_name" content="Exam Darpan">
    
    <script type="application/ld+json">
    {json.dumps(schema_data, ensure_ascii=False)}
    </script>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <header class="header">
        <div class="container">
            <a href="/" class="logo">Exam Darpan</a>
        </div>
    </header>
    <main class="container content-area">
        <article class="post-article">
            <nav class="breadcrumb">
                <a href="/">Home</a> / <span>{category}</span>
            </nav>
            <h1>{title}</h1>
            <div class="post-meta">
                <span>Update: {updated_at[:10]}</span>
            </div>
            <div class="article-body">
                {content}
            </div>
        </article>
    </main>
    <footer class="footer">
        <div class="container">
            <p>&copy; {datetime.now().year} Exam Darpan. All Rights Reserved.</p>
        </div>
    </footer>
</body>
</html>"""

def generate_sitemaps(posts, categories):
    now_utc = format_w3c_date()

    # 1. Post Sitemap
    post_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in posts:
        slug = clean_slug(p.get("slug"))
        if not slug:
            continue
        mod = format_w3c_date(p.get("updatedAt") or p.get("createdAt"))
        post_xml.append(f"  <url>\n    <loc>{SITE_DOMAIN}/article/{slug}</loc>\n    <lastmod>{mod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>")
    post_xml.append('</urlset>')
    with open(os.path.join(OUTPUT_DIR, "post-sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(post_xml))

    # 2. Category Sitemap
    cat_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for cat in sorted(categories):
        cat_slug = clean_slug(cat)
        if cat_slug:
            cat_xml.append(f"  <url>\n    <loc>{SITE_DOMAIN}/{cat_slug}</loc>\n    <lastmod>{now_utc}</lastmod>\n    <changefreq>hourly</changefreq>\n    <priority>0.9</priority>\n  </url>")
    cat_xml.append('</urlset>')
    with open(os.path.join(OUTPUT_DIR, "category-sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(cat_xml))

    # 3. Page Sitemap
    pages = ["", "about-us", "contact", "privacy-policy", "disclaimer", "terms-and-conditions"]
    page_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        page_url = f"{SITE_DOMAIN}" if page == "" else f"{SITE_DOMAIN}/{page}"
        page_xml.append(f"  <url>\n    <loc>{page_url}</loc>\n    <lastmod>{now_utc}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>")
    page_xml.append('</urlset>')
    with open(os.path.join(OUTPUT_DIR, "page-sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(page_xml))

    # 4. Sitemap Index
    index_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <sitemap>\n    <loc>{SITE_DOMAIN}/post-sitemap.xml</loc>\n    <lastmod>{now_utc}</lastmod>\n  </sitemap>',
        f'  <sitemap>\n    <loc>{SITE_DOMAIN}/category-sitemap.xml</loc>\n    <lastmod>{now_utc}</lastmod>\n  </sitemap>',
        f'  <sitemap>\n    <loc>{SITE_DOMAIN}/page-sitemap.xml</loc>\n    <lastmod>{now_utc}</lastmod>\n  </sitemap>',
        '</sitemapindex>'
    ]
    with open(os.path.join(OUTPUT_DIR, "sitemap_index.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_xml))
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_xml))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ARTICLE_DIR, exist_ok=True)

    print("Attempting to load articles...")
    posts = fetch_posts_via_admin()
    if not posts:
        print("Admin SDK not available or empty. Trying public REST API...")
        posts = fetch_posts_via_rest()

    if not posts:
        print("Warning: No remote posts found. Scanning existing HTML in public/article...")
        existing_files = os.listdir(ARTICLE_DIR) if os.path.exists(ARTICLE_DIR) else []
        for file in existing_files:
            if file.endswith(".html") and file != "index.html":
                posts.append({"slug": file.replace(".html", ""), "title": file.replace(".html", "").replace("-", " ").title()})

    print(f"Processing {len(posts)} articles...")
    categories = set(["recruitment", "admit-card", "result", "answer-key"])
    for post in posts:
        slug = clean_slug(post.get("slug"))
        if not slug:
            continue
        cat = post.get("category")
        if cat:
            categories.add(cat)
        # Generate static HTML
        try:
            with open(os.path.join(ARTICLE_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
                f.write(build_article_html(post))
        except Exception as e:
            print(f"Error writing HTML for {slug}: {e}")

    generate_sitemaps(posts, categories)
    print("Static build and Sitemaps finished successfully!")

if __name__ == "__main__":
    main()
