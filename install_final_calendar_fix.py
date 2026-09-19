from pathlib import Path
import re

p = Path("public/all-india-exam-calendar.html")
s = p.read_text(encoding="utf-8")

# Remove existing calendar engines.
s = re.sub(
    r"<script\b[^>]*>.*?</script>",
    "",
    s,
    flags=re.I | re.S
)

# Make sure Firebase config is loaded before module engine.
marker = '<script src="/firebase-config.js"></script>'
if marker not in s:
    s = s.replace("</head>", marker + "\n</head>", 1)

engine = r'''
<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js";
import {
  getFirestore,
  collection,
  getDocs,
  query,
  where
} from "https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js";

(() => {

  const calendar = document.getElementById("calendar");
  const filters = document.getElementById("calendar-filters");

  if (!calendar) return;

  if (!window.FIREBASE_CONFIG) {
    calendar.innerHTML =
      '<div class="empty">Firebase configuration unavailable.</div>';
    console.error("EXAM DARPAN: FIREBASE_CONFIG missing");
    return;
  }

  const app = initializeApp(window.FIREBASE_CONFIG);
  const db = getFirestore(app);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let posts = [];
  let activeCategory = "all";

  function esc(v) {
    return String(v ?? "").replace(/[&<>"']/g, c => ({
      "&":"&amp;",
      "<":"&lt;",
      ">":"&gt;",
      '"':"&quot;",
      "'":"&#39;"
    }[c]));
  }

  function toDate(v) {

    if (!v) return null;

    if (typeof v === "string") {

      const value = v.trim();

      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const d = new Date(value + "T23:59:59");
        return Number.isNaN(d.getTime()) ? null : d;
      }

      const d = new Date(value);
      return Number.isNaN(d.getTime()) ? null : d;
    }

    if (v && typeof v.toDate === "function") {
      const d = v.toDate();
      return Number.isNaN(d.getTime()) ? null : d;
    }

    return null;
  }

  function makeDate(day, month, year) {

    const d = new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
      23,
      59,
      59
    );

    if (
      Number.isNaN(d.getTime()) ||
      d.getDate() !== Number(day) ||
      d.getMonth() !== Number(month) - 1 ||
      d.getFullYear() !== Number(year)
    ) {
      return null;
    }

    return d;
  }

  function dateFromText(text, patterns) {

    for (const pattern of patterns) {

      const m = text.match(pattern);

      if (!m) continue;

      const d = makeDate(m[1], m[2], m[3]);

      if (d) return d;
    }

    return null;
  }

  function textOf(post) {

    return [
      post.title,
      post.excerpt,
      post.content,
      ...(Array.isArray(post.tags) ? post.tags : [])
    ]
      .filter(Boolean)
      .join(" ");
  }

  /*
   * Rajasthan detection is deliberately aggressive.
   * A Rajasthan-specific post must NEVER leak into All India.
   */
  function isRajasthan(post) {

    const region = String(post.region || "")
      .trim()
      .toLowerCase();

    if (region === "rajasthan") return true;

    const category = String(post.category || "")
      .trim()
      .toLowerCase();

    if (/rajasthan\s*jobs/.test(category)) return true;

    const text = textOf(post);

    return /(
      \brajasthan\b|
      \brpsc\b|
      \brssb\b|
      \brsmssb\b|
      \breet\b|
      \brajasthan\s+police\b|
      \brajasthan\s+cet\b|
      \brvunl\b|
      \brajcrb\b|
      \banuprati\b|
      राजस्थान|
      राजस्थानी|
      अनुप्रति|
      आरपीएससी|
      आरएसएसबी|
      आरएसएमएसएसबी
    )/ix.test(text);
  }

  function categoryOf(post) {

    const title = String(post.title || "");
    const content = textOf(post);

    const combined = (title + " " + content).toLowerCase();

    /*
     * Exact category normalization.
     * More specific categories are checked first.
     */

    if (/admit\s*card|admit-card|hall\s*ticket|call\s*letter|exam\s*city|city\s*intimation|प्रवेश\s*पत्र|एडमिट\s*कार्ड/i.test(combined)) {
      return "Admit Card";
    }

    if (/answer\s*key|answer-key|उत्तर\s*कुंजी/i.test(combined)) {
      return "Answer Key";
    }

    if (/result|results|score\s*card|scorecard|परिणाम|रिजल्ट/i.test(combined)) {
      return "Results";
    }

    if (/syllabus|पाठ्यक्रम/i.test(combined)) {
      return "Syllabus";
    }

    if (
      /recruitment|recruit|vacancy|vacancies|bharti|भर्ती|posts?|पदों|apply\s*online|आवेदन\s*शुरू|आवेदन\s*करें/i
        .test(combined)
    ) {
      return "Government Jobs";
    }

    /*
     * Preserve useful explicit CMS categories where applicable.
     */
    const raw = String(post.category || "").trim();

    if (
      [
        "Government Jobs",
        "Admit Card",
        "Results",
        "Answer Key",
        "Syllabus",
        "Latest Updates"
      ].includes(raw)
    ) {
      return raw;
    }

    return "Latest Updates";
  }

  function getDeadline(post) {

    const direct = [
      "lastDate",
      "last_date",
      "applicationLastDate",
      "application_last_date",
      "applicationDeadline",
      "application_deadline",
      "closingDate",
      "closing_date",
      "deadline"
    ];

    for (const key of direct) {

      const d = toDate(post[key]);

      if (d) return d;
    }

    const text = textOf(post);

    return dateFromText(text, [

      /(?:last\s*date|last\s*date\s*to\s*apply|application\s*last\s*date|deadline|closing\s*date)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i,

      /(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तारीख|आवेदन\s*करने\s*की\s*अंतिम\s*तिथि)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i

    ]);
  }

  function getExamDate(post) {

    const direct = [
      "examDate",
      "exam_date",
      "examDateTime",
      "exam_date_time"
    ];

    for (const key of direct) {

      const d = toDate(post[key]);

      if (d) return d;
    }

    const text = textOf(post);

    return dateFromText(text, [

      /(?:exam\s*date|exam\s*on|examination\s*date)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i,

      /(?:परीक्षा\s*तिथि|परीक्षा\s*की\s*तिथि|परीक्षा\s*तारीख)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i

    ]);
  }

  function getStartDate(post) {

    const direct = [
      "applicationStartDate",
      "application_start_date",
      "startDate",
      "start_date"
    ];

    for (const key of direct) {

      const d = toDate(post[key]);

      if (d) return d;
    }

    const text = textOf(post);

    return dateFromText(text, [

      /(?:application\s*start|application\s*starts|apply\s*from|registration\s*starts?)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i,

      /(?:आवेदन\s*शुरू|आवेदन\s*प्रारंभ|आवेदन\s*आरंभ)\D{0,20}(\d{1,2})[\/.\-](\d{1,2})[\/.\-](20\d{2})/i

    ]);
  }

  function expiryOf(post) {
    return getDeadline(post) || getExamDate(post);
  }

  function isActive(post) {

    const deadline = getDeadline(post);
    const exam = getExamDate(post);

    /*
     * A calendar item without ANY reliable date is not shown.
     * This prevents fake LIVE + Not announced cards.
     */
    if (!deadline && !exam) return false;

    /*
     * If application deadline exists, use it as primary expiry.
     */
    if (deadline) {
      return deadline >= today;
    }

    /*
     * Otherwise keep until exam date.
     */
    return exam >= today;
  }

  function formatDate(d) {

    if (!d) return "To be announced";

    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    });
  }

  function daysLeft(d) {

    if (!d) return "";

    const target = new Date(d);
    target.setHours(0, 0, 0, 0);

    const n = Math.ceil(
      (target.getTime() - today.getTime()) / 86400000
    );

    if (n < 0) return "";
    if (n === 0) return "Today";

    return n + " days left";
  }

  function createFilters() {

    if (!filters) return;

    const categories = [
      ...new Set(
        posts
          .filter(p => !isRajasthan(p))
          .filter(isActive)
          .map(categoryOf)
      )
    ].sort();

    filters.innerHTML =
      '<button class="filter active" data-filter="all">All</button>' +
      categories.map(category =>
        '<button class="filter" data-filter="' +
        esc(category) +
        '">' +
        esc(category) +
        "</button>"
      ).join("");

    filters
      .querySelectorAll(".filter")
      .forEach(button => {

        button.addEventListener("click", () => {

          filters
            .querySelectorAll(".filter")
            .forEach(x =>
              x.classList.remove("active")
            );

          button.classList.add("active");

          activeCategory =
            button.dataset.filter || "all";

          render();
        });

      });
  }

  function render() {

    const rows = posts
      .filter(p => p.status === "published")

      /*
       * HARD SEPARATION:
       * Rajasthan never appears on All India calendar.
       */
      .filter(p => !isRajasthan(p))

      /*
       * Only genuinely active/date-backed entries.
       */
      .filter(isActive)

      .filter(p =>
        activeCategory === "all" ||
        categoryOf(p) === activeCategory
      )

      .sort((a, b) => {

        const ad = expiryOf(a) ||
          new Date(8640000000000000);

        const bd = expiryOf(b) ||
          new Date(8640000000000000);

        return ad - bd;
      });

    if (!rows.length) {

      calendar.innerHTML =
        '<div class="empty">' +
        "अभी कोई active All India exam update उपलब्ध नहीं है।" +
        "</div>";

      return;
    }

    calendar.innerHTML =
      rows.map(post => {

        const start = getStartDate(post);
        const deadline = getDeadline(post);
        const exam = getExamDate(post);

        const countdown =
          daysLeft(deadline || exam);

        const slug =
          String(post.slug || "").trim();

        const articleUrl =
          "/article.html?slug=" +
          encodeURIComponent(slug);

        const apply =
          post.applyOnlineUrl ||
          post.officialWebsiteUrl ||
          post.officialNotificationUrl ||
          "";

        const category =
          categoryOf(post);

        return `
          <article
            class="item"
            data-calendar="all-india"
            data-calendar-entry="all-india"
            data-region="all-india"
            data-category="${esc(category)}">

            <div class="item-top">

              <div>

                <span class="category">
                  ${esc(category)}
                </span>

                <h2>
                  <a href="${articleUrl}">
                    ${esc(post.title || "Untitled")}
                  </a>
                </h2>

              </div>

              <span class="status">
                LIVE
              </span>

            </div>

            <div class="meta">

              <div class="meta-box">

                <small>
                  Application Starts
                </small>

                <strong>
                  ${
                    start
                      ? esc(formatDate(start))
                      : "Not announced"
                  }
                </strong>

              </div>

              <div class="meta-box">

                <small>
                  Last Date
                </small>

                <strong>

                  ${
                    deadline
                      ? esc(formatDate(deadline))
                      : "Not announced"
                  }

                  ${
                    countdown
                      ? "<br><small>" +
                        esc(countdown) +
                        "</small>"
                      : ""
                  }

                </strong>

              </div>

              <div class="meta-box">

                <small>
                  Exam Date
                </small>

                <strong>

                  ${
                    exam
                      ? esc(formatDate(exam))
                      : "To be announced"
                  }

                </strong>

              </div>

            </div>

            <div class="actions">

              <a
                class="details"
                href="${articleUrl}">
                Details →
              </a>

              ${
                apply
                  ? `
                    <a
                      class="apply"
                      href="${esc(apply)}"
                      target="_blank"
                      rel="noopener">
                      Apply / Official Link →
                    </a>
                  `
                  : ""
              }

            </div>

          </article>
        `;

      }).join("");
  }

  async function loadPosts() {

    calendar.innerHTML =
      '<div class="empty">' +
      "Loading live All India updates…" +
      "</div>";

    try {

      const q = query(
        collection(db, "posts"),
        where("status", "==", "published")
      );

      const snap = await getDocs(q);

      posts = snap.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      createFilters();
      render();

    } catch (error) {

      console.error(
        "EXAM DARPAN calendar:",
        error
      );

      calendar.innerHTML =
        '<div class="empty">' +
        "All India updates load नहीं हो पाए।" +
        "</div>";
    }
  }

  loadPosts();

})();
</script>
'''

pos = s.lower().rfind("</body>")

if pos < 0:
    raise SystemExit("ERROR: </body> not found")

s = s[:pos] + engine + "\n" + s[pos:]

p.write_text(s, encoding="utf-8")

print("✓ FINAL CALENDAR ENGINE INSTALLED")
print("✓ RAJASTHAN HARD FILTER INSTALLED")
print("✓ CATEGORY NORMALIZATION INSTALLED")
print("✓ DEADLINE FALLBACK INSTALLED")
print("✓ EXAM DATE FALLBACK INSTALLED")
print("✓ START DATE FALLBACK INSTALLED")
print("✓ UNDated fake LIVE entries removed")
