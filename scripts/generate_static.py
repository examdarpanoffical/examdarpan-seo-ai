import os
import re
import html
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore

SITE_DOMAIN = "https://examdarpan.in"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
ARTICLE_DIR = os.path.join(OUTPUT_DIR, "article")

def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default application credentials if running in GCP/Firebase environment
            firebase_admin.initialize_app()
    return firestore.client()

def format_w3c_date(dt):
    if not dt:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def clean_slug(slug):
    slug = str(slug).strip().lower()
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    return re.sub(r'-+', '-', slug).strip('-')

def build_article_html(post):
    title = html.escape(post.get("title", "Exam Darpan Update"))
    description = html.escape(post.get("summary") or post.get("metaDescription") or (post.get("title", "")[:155]))
    slug = clean_slug(post.get("slug", ""))
    content = post.get("content", "")
    category = post.get("category", "General")
    
    canonical_url = f"{SITE_DOMAIN}/article/{slug}"
    created_at = format_w3c_date(post.get("createdAt"))
    updated_at = format_w3c_date(post.get("updatedAt") or post.get("createdAt"))

    schema_json = f"""{{
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": {html.escape(repr(title))},
      "datePublished": "{created_at}",
      "dateModified": "{updated_at}",
      "mainEntityOfPage": "{canonical_url}",
      "publisher": {{
        "@type": "Organization",
        "name": "Exam Darpan",
        "logo": {{
          "@type": "ImageObject",
          "url": "{SITE_DOMAIN}/assets/logo.png"
        }}
      }}
    }}"""

    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Exam Darpan</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical_url}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <!-- Open Graph -->
    <meta property="og:locale" content="hi_IN">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:site_name" content="Exam Darpan">
    
    <!-- Structured Data -->
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
                <a href="/">Home</a> / <span>{html.escape(category)}</span>
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
    for cat in categories:
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
        
    # Symlink/copy sitemap.xml to sitemap_index.xml for legacy crawlers
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_xml))

def main():
    os.makedirs(ARTICLE_DIR, exist_ok=True)
    db = init_firebase()
    
    docs = db.collection("posts").where("status", "==", "published").stream()
    posts = [d.to_dict() for d in docs if d.to_dict().get("slug")]
    
    print(f"Generating static pages for {len(posts)} articles...")
    categories = set()
    for post in posts:
        slug = clean_slug(post["slug"])
        cat = post.get("category")
        if cat:
            categories.add(cat)
            
        # Write to public/article/<slug>.html
        file_path = os.path.join(ARTICLE_DIR, f"{slug}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(build_article_html(post))

    static_pages = ["", "about-us", "contact", "privacy-policy", "disclaimer", "terms-and-conditions"]
    generate_sitemaps(posts, categories, static_pages)
    print("Static build and Sitemaps generated successfully!")

if __name__ == "__main__":
    main()
