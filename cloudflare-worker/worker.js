/**
 * Exam Darpan secure publish trigger.
 * Secrets/variables: FIREBASE_API_KEY, FIREBASE_ADMIN_UID, GITHUB_TOKEN, ALLOWED_ORIGIN.
 */
const REPO = "examdarpanoffical/examdarpan-seo-ai";
const WORKFLOW = "static-seo-deploy.yml";
const BRANCH = "main";
const API = "https://api.github.com";

function cors(origin, allowed) {
  return {
    "Access-Control-Allow-Origin": origin === allowed ? allowed : "null",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin"
  };
}
function reply(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers }
  });
}
function ghHeaders(env) {
  return {
    "Accept": "application/vnd.github+json",
    "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "Exam-Darpan-Static-Quiz-Publisher",
    "Content-Type": "application/json"
  };
}
function toBase64Utf8(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}
async function putGitHubFile(env, path, content, message, existingSha) {
  const url = `${API}/repos/${REPO}/contents/${path}`;
  let sha = existingSha || null;
  if (!sha) {
    const check = await fetch(url, { headers: ghHeaders(env) });
    if (check.status === 200) {
      const old = await check.json();
      sha = old.sha;
    } else if (check.status !== 404) {
      throw new Error("GitHub file check failed (" + check.status + ")");
    }
  }
  const response = await fetch(url, {
    method: "PUT",
    headers: ghHeaders(env),
    body: JSON.stringify({
      message,
      content: toBase64Utf8(content),
      branch: BRANCH,
      ...(sha ? { sha } : {})
    })
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.message || "GitHub could not save " + path);
  }
  return response.json();
}
function safeSlug(value) {
  return String(value || "").toLowerCase().trim()
    .replace(/[^a-z0-9-]+/g, "-").replace(/-+/g, "-")
    .replace(/^-|-$/g, "").slice(0, 90);
}
function prepareQuizHtml(html, slug, title) {
  let source = String(html || "").replace(/^\uFEFF/, "");
  if (!/^\s*(<!doctype\s+html|<html)/i.test(source)) {
    throw new Error("Uploaded file must be a complete HTML document.");
  }
  const canonical = `https://examdarpan.in/mock-tests/${slug}`;
  const redirect = `<script id="ed-primary-domain-redirect">(function(){var h=location.hostname.toLowerCase();if(h==="examdarpan-dd963.web.app"||h==="examdarpan-dd963.firebaseapp.com"){location.replace("${canonical}"+location.search+location.hash)}})();</script>`;
  if (/<link\b[^>]*rel=["']canonical["'][^>]*>/i.test(source)) {
    source = source.replace(/<link\b[^>]*rel=["']canonical["'][^>]*>/i,
      `<link rel="canonical" href="${canonical}">`);
  } else {
    source = source.replace(/<head\b[^>]*>/i, m => m + `\n<link rel="canonical" href="${canonical}">\n`);
  }
  if (!source.includes('id="ed-primary-domain-redirect"')) {
    source = source.replace(/<\/head\s*>/i, redirect + "\n</head>");
  }
  if (!/<title\b/i.test(source)) {
    source = source.replace(/<head\b[^>]*>/i, m => m + `<title>${title.replace(/[&<>]/g, "")} | Exam Darpan</title>`);
  }
  return source;
}
async function publishHtmlQuiz(env, payload) {
  const title = String(payload.title || "").trim().slice(0, 160);
  const slug = safeSlug(payload.slug);
  const html = String(payload.html || "");
  if (!title) throw new Error("Quiz title is required.");
  if (slug.length < 3) throw new Error("Slug must contain at least 3 letters or numbers.");
  if (!html || html.length > 1500000) throw new Error("HTML file is empty or exceeds the 1.5 MB limit.");
  const cleanHtml = prepareQuizHtml(html, slug, title);
  const path = `public/mock-tests/${slug}.html`;
  const check = await fetch(`${API}/repos/${REPO}/contents/${path}?ref=${BRANCH}`, { headers: ghHeaders(env) });
  if (check.status === 200) throw new Error("This quiz URL already exists. Choose a new slug.");
  if (check.status !== 404) throw new Error("Could not verify whether this quiz URL already exists.");

  const manifestPath = "public/mock-tests/manifest.json";
  const manifestResponse = await fetch(`${API}/repos/${REPO}/contents/${manifestPath}?ref=${BRANCH}`, { headers: ghHeaders(env) });
  let manifest = { quizzes: [] }, manifestSha = null;
  if (manifestResponse.status === 200) {
    const file = await manifestResponse.json();
    manifestSha = file.sha;
    const binary = atob(file.content.replace(/\s/g, ""));
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
    manifest = JSON.parse(new TextDecoder().decode(bytes));
  } else if (manifestResponse.status !== 404) {
    throw new Error("Could not read the static mock-test list.");
  }
  if (!Array.isArray(manifest.quizzes)) manifest.quizzes = [];
  manifest.quizzes = manifest.quizzes.filter(x => x && x.slug !== slug);
  manifest.quizzes.unshift({ slug, title, url: `/mock-tests/${slug}`, publishedAt: new Date().toISOString() });

  await putGitHubFile(env, path, cleanHtml, `Publish static mock test: ${slug}`);
  await putGitHubFile(env, manifestPath, JSON.stringify(manifest, null, 2) + "\n",
    `Update static mock-test listing: ${slug}`, manifestSha);

  return { published: true, slug, url: `https://examdarpan.in/mock-tests/${slug}`, message: "Quiz committed to GitHub. Hosting deployment will publish it." };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowed = env.ALLOWED_ORIGIN || "https://examdarpan.in";
    const headers = cors(origin, allowed);
    if (request.method === "OPTIONS") {
      if (origin !== allowed) return new Response(null, { status: 403 });
      return new Response(null, { status: 204, headers });
    }
    if (origin !== allowed) return reply({ error: "Origin not allowed" }, 403, headers);
    if (request.method !== "POST") return reply({ error: "Method not allowed" }, 405, headers);
    const match = (request.headers.get("Authorization") || "").match(/^Bearer\s+(.+)$/i);
    if (!match) return reply({ error: "Sign in as admin first" }, 401, headers);
    if (!env.FIREBASE_API_KEY || !env.FIREBASE_ADMIN_UID || !env.GITHUB_TOKEN)
      return reply({ error: "Trigger is not configured" }, 503, headers);
    try {
      const verify = await fetch(
        `https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${encodeURIComponent(env.FIREBASE_API_KEY)}`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ idToken: match[1] }) }
      );
      if (!verify.ok) return reply({ error: "Firebase login token invalid or expired" }, 401, headers);
      const identity = await verify.json();
      const user = Array.isArray(identity.users) ? identity.users[0] : null;
      if (!user || user.localId !== env.FIREBASE_ADMIN_UID || user.disabled === true)
        return reply({ error: "Not authorized" }, 403, headers);

      const payload = await request.json().catch(() => ({}));
      if (payload.action === "publish-html-quiz") {
        const result = await publishHtmlQuiz(env, payload);
        return reply(result, 201, headers);
      }

      const dispatch = await fetch(
        `${API}/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: "POST",
          headers: ghHeaders(env),
          body: JSON.stringify({ ref: BRANCH })
        }
      );
      if (dispatch.status !== 204)
        return reply({ error: "GitHub could not queue build; check Worker/GitHub configuration" }, 502, headers);
      return reply({ queued: true, message: "Static SEO rebuild queued" }, 202, headers);
    } catch (error) {
      return reply({ error: error?.message || "Publish request failed; check Worker logs" }, 502, headers);
    }
  }
};
