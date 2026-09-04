#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=========================================="
echo " Exam Darpan Automatic SEO Setup"
echo "=========================================="

mkdir -p .github/workflows

cp scripts/generate_static.py scripts/generate_static.py.backup

echo "[1/4] Creating service-account based static builder..."

python3 - <<'PY'
from pathlib import Path

p = Path("scripts/generate_static.py")
s = p.read_text(encoding="utf-8")

start = s.index("def fetch():")
end = s.index("\ndef esc(", start)

new_fetch = r'''def fetch():
    """Fetch published posts using Firebase service-account credentials."""
    import os
    import requests
    import firebase_admin
    from firebase_admin import credentials, firestore

    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()

    if not raw:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON secret/environment variable is missing."
        )

    try:
        service_account_info = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON."
        ) from e

    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(service_account_info)
        )

    db = firestore.client()

    docs = (
        db.collection("posts")
        .where("status", "==", "published")
        .limit(300)
        .stream()
    )

    out = []

    for doc in docs:
        p = doc.to_dict()
        p["id"] = doc.id

        if p.get("status") == "published" and p.get("slug"):
            out.append(p)

    return sorted(
        out,
        key=lambda x: str(x.get("publishedAt") or ""),
        reverse=True
    )
'''

p.write_text(s[:start] + new_fetch + s[end:], encoding="utf-8")

print("generate_static.py updated.")
PY

echo "[2/4] Creating automatic SEO deployment workflow..."

cat > .github/workflows/static-seo-deploy.yml <<'YAML'
name: Exam Darpan Automatic SEO Deploy

on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: examdarpan-static-seo
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r monitor_requirements.txt

      - name: Build static SEO pages
        env:
          FIREBASE_SERVICE_ACCOUNT_JSON: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
        run: |
          python scripts/generate_static.py

      - name: Verify generated SEO files
        run: |
          test -f public/sitemap.xml
          test -f public/robots.txt || true
          echo "Generated article pages:"
          find public -maxdepth 1 -type f -name "*.html" | wc -l

      - name: Install Firebase CLI
        run: npm install -g firebase-tools

      - name: Deploy Firebase Hosting
        env:
          GOOGLE_APPLICATION_CREDENTIALS_JSON: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
        run: |
          printf '%s' "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/firebase-service-account.json
          export GOOGLE_APPLICATION_CREDENTIALS=/tmp/firebase-service-account.json
          firebase use examdarpan-dd963
          firebase deploy --only hosting --non-interactive

      - name: Cleanup credentials
        if: always()
        run: rm -f /tmp/firebase-service-account.json
YAML

echo "[3/4] Creating robots.txt if missing..."

if [ ! -f public/robots.txt ]; then
cat > public/robots.txt <<'ROBOTS'
User-agent: *
Allow: /

Sitemap: https://examdarpan.in/sitemap.xml
ROBOTS
fi

echo "[4/4] Checking configuration..."

python3 -m json.tool firebase.json >/dev/null

echo
echo "=========================================="
echo " Setup files created successfully."
echo "=========================================="
echo
echo "Created:"
echo "  .github/workflows/static-seo-deploy.yml"
echo "  public/robots.txt (if missing)"
echo
echo "Backup:"
echo "  scripts/generate_static.py.backup"
echo
echo "IMPORTANT:"
echo "The GitHub repository and FIREBASE_SERVICE_ACCOUNT_JSON"
echo "secret must be configured before the GitHub workflow can run."
echo
echo "Next:"
echo "  1. Push this project to GitHub"
echo "  2. Add FIREBASE_SERVICE_ACCOUNT_JSON secret"
echo "  3. Run the workflow once manually"
echo
