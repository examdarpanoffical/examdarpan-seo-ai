Exam Darpan automation flow

1. official-monitor.yml checks the configured Rajasthan official sources every 15 minutes.
2. New source material is converted into a Firestore draft using Gemini.
3. Draft is NOT published automatically.
4. Admin reviews the draft in https://examdarpan.in/adr and clicks Publish.
5. telegram-publisher.yml checks published Firestore posts every 5 minutes.
6. A published post is sent to the Telegram channel once, then Firestore gets telegramSentAt.

Required GitHub Actions secrets:
- FIREBASE_SERVICE_ACCOUNT_JSON
- GEMINI_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Security:
- Never put service-account JSON, Gemini API keys, or Telegram bot tokens in public/.
- Telegram posting is server-side in GitHub Actions, not browser JavaScript.
