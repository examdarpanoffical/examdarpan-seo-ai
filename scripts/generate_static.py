import os
import re
import json
import html
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore

SITE_DOMAIN = "https://examdarpan.in"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
ARTICLE_DIR = os.path.join(OUTPUT_DIR, "article")

def init_firebase():
    """Initialize Firebase Admin securely from Secret JSON string, file path, or default app."""
    if firebase_admin._apps:
        return firestore.client()

    # Method 1: Direct JSON string from GitHub Secret (Best & Safest)
    cred_json_str = (
        os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        or os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY_CONTENT")
    )
    if cred_json_str and cred_json_str.strip().startswith("{"):
        try:
            cred_dict = json.loads(cred_json_str)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Successfully initialized Firebase Admin from JSON environment variable.")
            return firestore.client()
        except Exception as e:
            print(f"Warning: Failed to parse JSON secret directly: {e}")

    # Method 2: File path if provided
    cred_file = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_file and os.path.isfile(cred_file):
        try:
            cred = credentials.Certificate(cred_file)
            firebase_admin.initialize_app(cred)
            print(f"Successfully initialized Firebase Admin from file: {cred_file}")
            return firestore.client()
        except Exception as e:
            print(f"Warning: Failed to initialize from file {cred_file}: {e}")

    # Method 3: Fallback to Default Credentials
    try:
        firebase_admin.initialize_app()
        print("Initialized Firebase Admin using Application Default Credentials.")
        return firestore.client()
    except Exception as e:
        print(f"Critical Error: Could not authenticate to Firebase: {e}")
        raise e

def format_w3c_date(dt):
    """Safely format Firestore Timestamp, datetime, string, or int into ISO 8601 UTC."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not dt:
        return now_str

    try:
        # Datetime or Firestore DatetimeWithNanoseconds
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Int or Float (Unix epoch timestamp)
        if isinstance(dt, (int, float)):
            if dt > 1e11:  # Milliseconds
                dt = dt / 1000.0
            return datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # String format (ISO, YYYY-MM-DD, etc.)
        if isinstance(dt, str):
            clean_str = dt.strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(clean_str)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                return datetime.strptime(clean_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Date parse warning for '{dt}': {e}. Using current time.")
        
    return now_str

def clean_slug(slug):
    slug = str(slug or "").strip().lower()
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    return re.sub(r'-+', '-', slug).strip('-')

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
    schema_json = json.dumps(schema_data, ensure_ascii=False)

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
    {schema_json}
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
                <span>Last Updated: {updated_at[:10]}</span>
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

def generate_sitemaps(posts, categories, static_pages):
    now_utc = format_w3c_date(datetime.now(timezone.utc))

    # 1. Post Sitemap
    post_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in posts:
        slug = clean_slug(p.get("slug"))
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
        cat_xml.append(f"  <url>\n    <loc>{SITE_DOMAIN}/{cat_slug}</loc>\n    <lastmod>{now_utc}</lastmod>\n    <changefreq>hourly</changefreq>\n    <priority>0.9</priority>\n  </url>")
    cat_xml.append('</urlset>')

    with open(os.path.join(OUTPUT_DIR, "category-sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(cat_xml))

    # 3. Page Sitemap
    page_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in static_pages:
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
        
    # Legacy sitemap.xml
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_xml))

def main():
    os.makedirs(ARTICLE_DIR, exist_ok=True)
    db = init_firebase()

    print("Fetching documents from Firestore...")
    posts = []
    
    # Check 'posts' collection first, fallback to 'articles'
    for col_name in ["posts", "articles"]:
        try:
            docs = list(db.collection(col_name).stream())
            if docs:
                print(f"Found {len(docs)} documents in collection '{col_name}'.")
                for doc in docs:
                    data = doc.to_dict()
                    status = str(data.get("status", "published")).lower()
                    if status in ["draft", "trash"]:
                        continue
                    if not data.get("slug"):
                        data["slug"] = doc.id
                    posts.append(data)
                break
        except Exception as e:
            print(f"Notice: Failed to fetch from '{col_name}': {e}")

    print(f"Generating static HTML for {len(posts)} articles...")
    categories = set()
    for post in posts:
        slug = clean_slug(post["slug"])
        if not slug:
            continue

        cat = post.get("category")
        if cat:
            categories.add(cat)

        file_path = os.path.join(ARTICLE_DIR, f"{slug}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(build_article_html(post))

    static_pages = ["", "about-us", "contact", "privacy-policy", "disclaimer", "terms-and-conditions"]
    generate_sitemaps(posts, categories, static_pages)
    print("Static build and Sitemaps generated successfully!")

if __name__ == "__main__":
    main()
