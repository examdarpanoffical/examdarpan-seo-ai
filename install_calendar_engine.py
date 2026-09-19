from pathlib import Path
import re

p = Path("public/all-india-exam-calendar.html")
s = p.read_text(encoding="utf-8")

# Remove all existing executable scripts.
s = re.sub(
    r"<script\b[^>]*>.*?</script>",
    "",
    s,
    flags=re.I | re.S
)

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

const calendar = document.getElementById("calendar");
const filters = document.getElementById("calendar-filters");

if (calendar && window.FIREBASE_CONFIG) {
  const app = initializeApp(window.FIREBASE_CONFIG);
  const db = getFirestore(app);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#39;"
  }[c]));

  const dateOnly = v => {
    if (!v) return null;

    if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
      const d = new Date(v + "T23:59:59");
      return Number.isNaN(d.getTime()) ? null : d;
    }

    if (v && typeof v.toDate === "function") {
      const d = v.toDate();
      d.setHours(23,59,59,999);
      return d;
    }

    return null;
  };

  const formatDate = v => {
    const d = dateOnly(v);
    return d
      ? d.toLocaleDateString("en-IN", {
          day:"2-digit",
          month:"short",
          year:"numeric"
        })
      : "To be announced";
  };

  const regionOf = post => {
    const region = String(post.region || "").toLowerCase().trim();

    if (region === "rajasthan") return "rajasthan";
    if (region === "all-india") return "all-india";

    return String(post.category || "").toLowerCase().trim() ===
      "rajasthan jobs"
      ? "rajasthan"
      : "all-india";
  };

  const categoryOf = post =>
    String(post.category || "Latest Updates").trim();

  const expiryOf = post =>
    dateOnly(post.applicationLastDate) ||
    dateOnly(post.examDate);

  const isExpired = post => {
    const d = expiryOf(post);
    return d ? d < today : false;
  };

  const daysLeft = v => {
    const d = dateOnly(v);
    if (!d) return "";

    const n = Math.ceil((d - today) / 86400000);

    if (n < 0) return "";
    if (n === 0) return "Today";

    return n + " days left";
  };

  let posts = [];
  let activeCategory = "all";

  function createFilters() {
    if (!filters) return;

    const categories = [
      ...new Set(
        posts
          .filter(p => regionOf(p) === "all-india")
          .map(categoryOf)
          .filter(Boolean)
      )
    ].sort();

    filters.innerHTML =
      '<button class="filter active" data-filter="all">All</button>' +
      categories.map(c =>
        '<button class="filter" data-filter="' +
        esc(c) +
        '">' +
        esc(c) +
        "</button>"
      ).join("");

    filters.querySelectorAll(".filter").forEach(btn => {
      btn.addEventListener("click", () => {
        filters.querySelectorAll(".filter")
          .forEach(x => x.classList.remove("active"));

        btn.classList.add("active");
        activeCategory = btn.dataset.filter || "all";

        render();
      });
    });
  }

  function render() {
    const rows = posts
      .filter(p => p.status === "published")
      .filter(p => regionOf(p) === "all-india")
      .filter(p => !isExpired(p))
      .filter(p =>
        activeCategory === "all" ||
        categoryOf(p) === activeCategory
      )
      .sort((a,b) => {
        const ad = expiryOf(a) || new Date(8640000000000000);
        const bd = expiryOf(b) || new Date(8640000000000000);
        return ad - bd;
      });

    if (!rows.length) {
      calendar.innerHTML =
        '<div class="empty">अभी कोई active All India exam update उपलब्ध नहीं है.</div>';
      return;
    }

    calendar.innerHTML = rows.map(post => {
      const start = post.applicationStartDate || "";
      const last = post.applicationLastDate || "";
      const exam = post.examDate || "";
      const countdown = daysLeft(last || exam);

      const apply =
        post.applyOnlineUrl ||
        post.officialWebsiteUrl ||
        "";

      const slug = post.slug || "";
      const articleUrl =
        "/article.html?slug=" + encodeURIComponent(slug);

      return `
        <article
          class="item"
          data-calendar="all-india"
          data-calendar-entry="all-india"
          data-region="all-india"
          data-category="${esc(categoryOf(post))}">

          <div class="item-top">
            <div>
              <span class="category">${esc(categoryOf(post))}</span>

              <h2>
                <a href="${articleUrl}">
                  ${esc(post.title || "Untitled")}
                </a>
              </h2>
            </div>

            <span class="status">LIVE</span>
          </div>

          <div class="meta">
            <div class="meta-box">
              <small>Application Starts</small>
              <strong>${esc(
                start ? formatDate(start) : "Not announced"
              )}</strong>
            </div>

            <div class="meta-box">
              <small>Last Date</small>
              <strong>
                ${esc(
                  last ? formatDate(last) : "Not announced"
                )}
                ${
                  countdown
                    ? "<br><small>" + esc(countdown) + "</small>"
                    : ""
                }
              </strong>
            </div>

            <div class="meta-box">
              <small>Exam Date</small>
              <strong>${esc(
                exam ? formatDate(exam) : "To be announced"
              )}</strong>
            </div>
          </div>

          <div class="actions">
            <a class="details" href="${articleUrl}">
              Details →
            </a>

            ${
              apply
                ? '<a class="apply" href="' +
                  esc(apply) +
                  '" target="_blank" rel="noopener">' +
                  'Apply / Official Link →' +
                  '</a>'
                : ""
            }
          </div>
        </article>
      `;
    }).join("");
  }

  async function loadPosts() {
    calendar.innerHTML =
      '<div class="empty">Loading live All India updates…</div>';

    try {
      const q = query(
        collection(db, "posts"),
        where("status", "==", "published")
      );

      const snap = await getDocs(q);

      posts = snap.docs.map(d => ({
        id: d.id,
        ...d.data()
      }));

      createFilters();
      render();

    } catch (error) {
      console.error("EXAM DARPAN calendar:", error);

      calendar.innerHTML =
        '<div class="empty">All India updates load नहीं हो पाए।</div>';
    }
  }

  loadPosts();

} else if (calendar) {
  calendar.innerHTML =
    '<div class="empty">Firebase configuration unavailable.</div>';
}
</script>
'''

pos = s.lower().rfind("</body>")

if pos < 0:
    raise SystemExit("ERROR: </body> not found")

s = s[:pos] + engine + "\n" + s[pos:]

p.write_text(s, encoding="utf-8")

print("✓ CALENDAR ENGINE INSTALLED")
