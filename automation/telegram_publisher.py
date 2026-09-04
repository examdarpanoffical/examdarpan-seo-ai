import json, os, time
from datetime import datetime, timezone

import requests
import firebase_admin
from firebase_admin import credentials, firestore

SITE = "https://examdarpan.in"
ADMIN = "https://examdarpan.in/adr"


def get_db():
    if not firebase_admin._apps:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON secret is missing")
        firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
    return firestore.client()


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": False}, timeout=25)
    r.raise_for_status()


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID secrets are required")

    db = get_db()
    docs = list(db.collection("posts").where("status", "==", "published").limit(50).stream())
    docs.sort(key=lambda d: (d.to_dict().get("publishedAt") is not None, str(d.to_dict().get("publishedAt"))), reverse=True)
    sent = 0

    for snap in docs:
        p = snap.to_dict()
        if p.get("telegramSentAt"):
            continue
        title = str(p.get("title") or "Exam Darpan Update").strip()
        slug = str(p.get("slug") or "").strip()
        if not slug:
            print("SKIP no slug", snap.id)
            continue
        url = f"{SITE}/article/{slug}"
        category = str(p.get("category") or "Latest Update")
        message = f"🔔 Exam Darpan Update\n\n{title}\n\n📌 {category}\n\nपढ़ें: {url}"
        try:
            send_telegram(token, chat_id, message)
            snap.reference.update({"telegramSentAt": firestore.SERVER_TIMESTAMP, "telegramStatus": "sent"})
            sent += 1
            print("TELEGRAM SENT", snap.id, title)
            time.sleep(0.4)
        except Exception as e:
            snap.reference.update({"telegramStatus": "error", "telegramError": str(e)[:1000]})
            print("TELEGRAM ERROR", snap.id, repr(e))

    print(f"Done. Telegram posts sent: {sent}")


if __name__ == "__main__":
    main()
