"""Small, dependency-free agents for the Exam Darpan workflow MVP."""
from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

REQUIRED_FACTS = ["पदों की संख्या", "आवेदन शुरू", "अंतिम तिथि", "योग्यता", "आवेदन शुल्क", "आधिकारिक लिंक"]


def research_agent(topic: str, official_url: str, source_notes: str) -> dict:
    """Organize user-provided source material; this does not perform live web verification."""
    notes = source_notes.strip()
    missing = [fact for fact in REQUIRED_FACTS if fact.casefold() not in notes.casefold()]
    parsed = urlparse(official_url.strip()) if official_url.strip() else None
    valid_url = bool(parsed and parsed.scheme == "https" and parsed.netloc)
    return {
        "agent": "Recruitment Research Agent",
        "topic": topic.strip(),
        "official_url": official_url.strip(),
        "source_url_format_ok": valid_url,
        "source_notes": notes,
        "missing_facts": missing,
        "status": "SOURCE_NOTES_PROVIDED" if notes and valid_url else "NEEDS_SOURCE_REVIEW",
        "warning": "URL format is checked only; source authenticity and facts have not been independently verified.",
    }


def article_agent(research: dict) -> dict:
    topic = research.get("topic") or "सरकारी भर्ती अपडेट"
    url = research.get("official_url") or ""
    notes = research.get("source_notes") or ""
    title = f"{topic}: आवेदन, योग्यता और जरूरी जानकारी | Exam Darpan"
    description = f"{topic} की जरूरी जानकारी, आवेदन प्रक्रिया और आधिकारिक स्रोत देखें। आवेदन से पहले मूल नोटिफिकेशन जरूर पढ़ें।"
    source_line = f"आधिकारिक स्रोत: {url}" if url else "आधिकारिक स्रोत का लिंक अभी जोड़ना बाकी है।"
    article = (
        f"# {title}\n\n"
        f"## भर्ती का संक्षिप्त विवरण\n\n"
        f"{topic} से संबंधित जानकारी नीचे दिए गए उपलब्ध स्रोत नोट्स पर आधारित ड्राफ्ट है। प्रकाशित करने से पहले सभी विवरण मूल अधिसूचना से मिलाएँ।\n\n"
        f"## उपलब्ध स्रोत जानकारी\n\n{notes or 'अभी स्रोत नोट्स नहीं दिए गए हैं।'}\n\n"
        f"## आवेदन से पहले ध्यान दें\n\n"
        f"पदों की संख्या, आवेदन की तारीखें, योग्यता, शुल्क और चयन प्रक्रिया मूल आधिकारिक नोटिफिकेशन से सत्यापित करें। कोई जानकारी उपलब्ध न हो तो अनुमान लगाकर न जोड़ें।\n\n"
        f"## महत्वपूर्ण आधिकारिक लिंक\n\n- {source_line}\n\n"
        f"Exam Darpan — Fast Exam Updates"
    )
    return {"agent": "Article Writing Agent", "title": title, "meta_description": description, "article_markdown": article}


def seo_audit_agent(research: dict, article: dict) -> dict:
    title = article.get("title", "")
    description = article.get("meta_description", "")
    body = article.get("article_markdown", "")
    issues = []
    if not title:
        issues.append("SEO title missing")
    elif len(title) > 70:
        issues.append(f"SEO title is {len(title)} characters; consider shortening it")
    if not description:
        issues.append("Meta description missing")
    elif len(description) > 160:
        issues.append(f"Meta description is {len(description)} characters; consider shortening it")
    if body.count("## ") < 3:
        issues.append("Add clear section headings")
    if not research.get("source_url_format_ok"):
        issues.append("A valid HTTPS official-source URL is missing")
    if research.get("missing_facts"):
        issues.append("Source notes may be missing: " + ", ".join(research["missing_facts"]))
    if re.search(r"\b(lorem ipsum|TODO|TBD)\b", body, re.I):
        issues.append("Placeholder text detected")
    return {"agent": "SEO Audit Agent", "title_length": len(title), "description_length": len(description), "issues": issues, "status": "REVIEW_REQUIRED" if issues else "BASIC_CHECKS_PASSED", "note": "Basic text checks only; no live crawl, Google indexing check, or ranking prediction is performed."}


def social_media_agent(topic: str, article: dict, official_url: str) -> dict:
    link = official_url.strip() or "आधिकारिक लिंक लेख में जोड़ें"
    title = article.get("title", topic)
    whatsapp = f"📢 {topic}\n\nजरूरी जानकारी और आवेदन से पहले official notification जरूर पढ़ें।\n🔗 {link}\n\nEXAM DARPAN — Fast Exam Updates"
    telegram = f"📌 {topic}\n{title}\n\nमुख्य जानकारी पढ़ें और सभी तारीखें आधिकारिक नोटिफिकेशन से verify करें।\nOfficial link: {link}\n\n#ExamDarpan #SarkariNaukri #RajasthanJobs"
    instagram = f"{topic} 📢\n\nआवेदन से पहले योग्यता, तारीख और शुल्क official notification से जरूर check करें।\n\nअधिक जानकारी: {link}\n\n#ExamDarpan #GovtJobs #ExamUpdates"
    return {"agent": "Social Media Agent", "whatsapp": whatsapp, "telegram": telegram, "instagram": instagram}


def supervisor_workflow(topic: str, official_url: str, source_notes: str) -> dict:
    research = research_agent(topic, official_url, source_notes)
    article = article_agent(research)
    audit = seo_audit_agent(research, article)
    social = social_media_agent(topic, article, official_url)
    return {
        "supervisor": "AI Supervisor",
        "workflow": [research["agent"], article["agent"], audit["agent"], social["agent"]],
        "approval_required": True,
        "publish_enabled": False,
        "research": research,
        "article": article,
        "seo_audit": audit,
        "social_posts": social,
        "final_status": "HUMAN_REVIEW_REQUIRED",
    }
