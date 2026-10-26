"""Quality-gated, dependency-free agents for the Exam Darpan workflow MVP.

This module does not browse the web, verify source authenticity, or publish content.
It deliberately treats placeholders and unknown facts as blockers.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

REQUIRED_FACTS = [
    "पदों की संख्या", "आवेदन शुरू", "अंतिम तिथि",
    "योग्यता", "आवेदन शुल्क", "आधिकारिक लिंक",
]
UNKNOWN_MARKERS = (
    "पुष्टि बाकी", "पुष्टि होना बाकी", "पुष्टि नहीं", "जोड़ना बाकी",
    "नोटिफिकेशन मिलने पर", "उपलब्ध नहीं", "अभी नहीं", "पता नहीं",
    "confirm", "to be confirmed", "tbd", "todo", "unknown", "not available",
)


def _unknown_value(value: str) -> bool:
    cleaned = value.strip().casefold()
    return not cleaned or any(marker in cleaned for marker in UNKNOWN_MARKERS)


def _fact_values(notes: str) -> dict[str, str]:
    """Read simple 'label: value' lines without pretending to parse every PDF."""
    found: dict[str, str] = {}
    for line in notes.splitlines():
        if ":" not in line and "：" not in line:
            continue
        label, value = re.split(r"[:：]", line, maxsplit=1)
        label = label.strip().casefold()
        value = value.strip()
        for fact in REQUIRED_FACTS:
            if label == fact.casefold():
                found[fact] = value
    return found


def research_agent(topic: str, official_url: str, source_notes: str) -> dict:
    """Organize user notes and flag unknowns; no live web verification occurs."""
    notes = source_notes.strip()
    values = _fact_values(notes)
    missing = [fact for fact in REQUIRED_FACTS if _unknown_value(values.get(fact, ""))]
    parsed = urlparse(official_url.strip()) if official_url.strip() else None
    valid_url_format = bool(
        parsed and parsed.scheme == "https" and parsed.netloc
        and "." in parsed.hostname if parsed and parsed.hostname else False
    )
    unknown_facts = [fact for fact in REQUIRED_FACTS if fact in values and _unknown_value(values[fact])]
    return {
        "agent": "Recruitment Research Agent",
        "topic": topic.strip(),
        "official_url": official_url.strip(),
        "source_url_format_ok": valid_url_format,
        "source_domain": parsed.hostname if valid_url_format else "",
        "source_authenticity_verified": False,
        "source_notes": notes,
        "fact_values": values,
        "missing_facts": missing,
        "unknown_facts": unknown_facts,
        "status": "NEEDS_SOURCE_REVIEW" if missing or not valid_url_format else "NOT_INDEPENDENTLY_VERIFIED",
        "warning": "HTTPS format alone does not prove a site is official. The URL, source document, dates, vacancies, eligibility, and fees have not been independently verified.",
    }


def article_agent(research: dict) -> dict:
    topic = (research.get("topic") or "सरकारी भर्ती अपडेट").strip()
    url = research.get("official_url") or ""
    notes = research.get("source_notes") or ""
    values = research.get("fact_values") or {}
    title = f"{topic}: योग्यता व आवेदन | Exam Darpan"
    if len(title) > 65:
        title = f"{topic} | Exam Darpan"
    description = (
        f"{topic} की योग्यता, आवेदन तिथि, शुल्क और चयन प्रक्रिया की जानकारी। "
        "आवेदन से पहले आधिकारिक अधिसूचना से सभी विवरण सत्यापित करें।"
    )
    source_line = f"आधिकारिक अधिसूचना: {url}" if url else "आधिकारिक अधिसूचना का लिंक जोड़ना बाकी है।"
    rows = []
    for fact in REQUIRED_FACTS:
        value = values.get(fact, "").strip()
        rows.append(f"- **{fact}:** {value if value else 'आधिकारिक अधिसूचना से पुष्टि बाकी'}")
    facts_section = "\n".join(rows)
    missing = research.get("missing_facts") or []
    readiness = "HOLD — आधिकारिक स्रोत और सभी जरूरी तथ्यों की जाँच बाकी है" if missing or not research.get("source_url_format_ok") else "DRAFT — तथ्यों का स्वतंत्र सत्यापन और मानव समीक्षा बाकी है"
    article = (
        f"# {title}\n\n"
        f"> **प्रकाशन स्थिति: {readiness}.** यह ड्राफ्ट दिए गए नोट्स से बना है; इसे सत्यापित भर्ती सूचना न मानें।\n\n"
        f"## भर्ती का संक्षिप्त परिचय\n\n"
        f"{topic} के बारे में पाठकों को आवेदन करने से पहले पदों, पात्रता, तारीखों और आवेदन प्रक्रिया की पुष्टि मूल आधिकारिक अधिसूचना से करनी चाहिए। नीचे केवल उपलब्ध नोट्स का सार है।\n\n"
        f"## भर्ती की मुख्य जानकारी\n\n{facts_section}\n\n"
        f"## योग्यता और आवेदन से पहले जाँच\n\n"
        "आवेदन करने से पहले अधिसूचना में दी गई शैक्षणिक योग्यता, आयु सीमा और छूट, श्रेणीवार शुल्क, आवश्यक दस्तावेज, आवेदन की अंतिम तारीख तथा फॉर्म में सुधार की शर्तें ध्यान से पढ़ें। यहाँ जिन विवरणों की पुष्टि नहीं है, उन्हें अनुमान से नहीं भरा गया है।\n\n"
        f"## आवेदन कैसे करें\n\n"
        "1. संबंधित विभाग की आधिकारिक वेबसाइट स्वयं खोलें।\n"
        "2. इसी भर्ती की मूल अधिसूचना और आवेदन निर्देश पढ़ें।\n"
        "3. पात्रता व तारीखें जाँचने के बाद ही आवेदन फॉर्म भरें।\n"
        "4. जमा करने से पहले विवरण जाँचें और रसीद/आवेदन संख्या सुरक्षित रखें।\n\n"
        f"## महत्वपूर्ण आधिकारिक लिंक\n\n- {source_line}\n\n"
        "## अक्सर पूछे जाने वाले सवाल\n\n"
        f"**इस भर्ती की अंतिम तारीख क्या है?** उपलब्ध स्रोत नोट्स में अंतिम तारीख की पुष्टि नहीं है; मूल अधिसूचना देखें।\n\n"
        f"**कौन आवेदन कर सकता है?** पात्रता की पुष्टि आधिकारिक अधिसूचना से करनी होगी।\n\n"
        f"**क्या यह जानकारी सत्यापित है?** नहीं। यह नोट्स-आधारित ड्राफ्ट है; प्रकाशन से पहले मूल स्रोत से हर तथ्य और लिंक की जाँच जरूरी है।\n\n"
        "## स्रोत नोट्स (संपादकीय जाँच के लिए)\n\n"
        f"{notes or 'कोई स्रोत नोट्स नहीं दिए गए हैं।'}\n\n"
        "Exam Darpan — Fast Exam Updates"
    )
    return {
        "agent": "Article Writing Agent",
        "title": title,
        "meta_description": description,
        "article_markdown": article,
        "publication_readiness": "HOLD" if missing or not research.get("source_url_format_ok") else "HUMAN_REVIEW_REQUIRED",
        "missing_facts": missing,
        "note": "Draft only. No source authenticity or fact has been independently verified.",
    }


def seo_audit_agent(research: dict, article: dict) -> dict:
    title = article.get("title", "")
    description = article.get("meta_description", "")
    body = article.get("article_markdown", "")
    issues = []
    recommendations = []
    if not title:
        issues.append("SEO title missing")
    elif len(title) > 65:
        recommendations.append(f"Title is {len(title)} characters; consider a concise, page-specific title")
    if not description:
        issues.append("Meta description missing")
    elif len(description) > 160:
        recommendations.append(f"Meta description is {len(description)} characters; shorten if useful without keyword stuffing")
    if body.count("## ") < 5:
        recommendations.append("Add useful, recruitment-specific sections supported by verified sources")
    if not research.get("source_url_format_ok"):
        issues.append("A valid HTTPS source URL is missing")
    if not research.get("source_authenticity_verified"):
        issues.append("Official source authenticity has not been independently verified")
    if research.get("missing_facts"):
        issues.append("Unconfirmed or missing facts: " + ", ".join(research["missing_facts"]))
    if re.search(r"\b(lorem ipsum|TODO|TBD)\b", body, re.I):
        issues.append("Placeholder text detected")
    if len(body.strip()) < 900:
        recommendations.append("Content is short; add only useful, verified details rather than padding")
    if "## अक्सर पूछे जाने वाले सवाल" not in body:
        recommendations.append("Consider concise FAQs only when they answer real reader questions")
    return {
        "agent": "SEO Audit Agent",
        "title_length": len(title),
        "description_length": len(description),
        "issues": issues,
        "recommendations": recommendations,
        "status": "HOLD" if issues else ("REVIEW_REQUIRED" if recommendations else "BASIC_CHECKS_PASSED"),
        "note": "These are basic content checks, not Google's ranking factors, live crawl, indexing status, or ranking predictions. No ranking is guaranteed.",
    }


def social_media_agent(topic: str, article: dict, official_url: str) -> dict:
    can_share = article.get("publication_readiness") == "HUMAN_REVIEW_REQUIRED" and bool(official_url.strip())
    if not can_share:
        hold = (
            f"⛔ DRAFT ONLY — {topic}\n"
            "अभी प्रकाशित/शेयर न करें। आधिकारिक स्रोत और जरूरी तथ्यों की पुष्टि बाकी है। "
            "सत्यापन व मानव समीक्षा के बाद ही लिंक और तारीखें साझा करें।"
        )
        return {
            "agent": "Social Media Agent",
            "status": "HOLD",
            "whatsapp": hold,
            "telegram": hold,
            "instagram": hold,
            "warning": "Social drafts are deliberately held until a source URL is supplied and required facts are present. URL authenticity still needs human verification.",
        }
    link = official_url.strip()
    title = article.get("title", topic)
    whatsapp = f"📢 {topic}\n\nयोग्यता, तारीख और आवेदन विवरण मूल अधिसूचना से जाँचकर ही आवेदन करें।\n🔗 आधिकारिक सूचना: {link}\n\nEXAM DARPAN — Fast Exam Updates"
    telegram = f"📌 {title}\n\nआवेदन से पहले मूल अधिसूचना में पात्रता, तारीख और शुल्क जाँचें।\nआधिकारिक सूचना: {link}\n\n#ExamDarpan #SarkariNaukri #RajasthanJobs"
    instagram = f"{topic} 📢\n\nआवेदन से पहले पात्रता, तारीख और शुल्क मूल अधिसूचना से जाँचें।\nआधिकारिक सूचना: {link}\n\n#ExamDarpan #GovtJobs #ExamUpdates"
    return {"agent": "Social Media Agent", "status": "DRAFT_REQUIRES_HUMAN_REVIEW", "whatsapp": whatsapp, "telegram": telegram, "instagram": instagram}


def supervisor_workflow(topic: str, official_url: str, source_notes: str) -> dict:
    research = research_agent(topic, official_url, source_notes)
    article = article_agent(research)
    audit = seo_audit_agent(research, article)
    social = social_media_agent(topic, article, official_url)
    blockers = list(research.get("missing_facts", []))
    if not research.get("source_url_format_ok"):
        blockers.insert(0, "आधिकारिक HTTPS स्रोत लिंक")
    if not research.get("source_authenticity_verified"):
        blockers.append("स्रोत की वास्तविक आधिकारिकता और सभी तथ्यों का स्वतंत्र सत्यापन")
    final_status = "HOLD_SOURCE_VERIFICATION" if blockers else "HUMAN_REVIEW_REQUIRED"
    return {
        "supervisor": "AI Supervisor",
        "workflow": [
            research["agent"], article["agent"], audit["agent"],
            social["agent"], "AI Supervisor",
        ],
        "approval_required": True,
        "publish_enabled": False,
        "final_status": final_status,
        "publication_blockers": blockers,
        "research": research,
        "article": article,
        "seo_audit": audit,
        "social_posts": social,
        "important_limit": "No live browsing, official-source authentication, Google Search Console connection, or auto-publishing is implemented in this MVP.",
    }
