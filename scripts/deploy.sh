#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Building crawler-readable article pages from published Firestore posts..."
python3 scripts/generate_static.py

echo "Using Firebase project examdarpan-dd963..."
firebase use examdarpan-dd963

echo "Deploying Firestore + Hosting..."
firebase deploy --only firestore,hosting

echo "Deploy complete."
