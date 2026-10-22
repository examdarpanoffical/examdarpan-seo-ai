/**
 * Exam Darpan secure publish trigger.
 * Worker secrets/variables:
 * FIREBASE_API_KEY, FIREBASE_ADMIN_UID, GITHUB_TOKEN, ALLOWED_ORIGIN.
 */
const REPO = "examdarpanoffical/examdarpan-seo-ai";
const WORKFLOW = "static-seo-deploy.yml";
const BRANCH = "main";

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
    const match = (request.headers.get("Authorization") || "").match(/^Bearer\\s+(.+)$/i);
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
      const dispatch = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: "POST",
          headers: {
            "Accept": "application/vnd.github+json",
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Exam-Darpan-Secure-Publish-Trigger",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ ref: BRANCH })
        }
      );
      if (dispatch.status !== 204)
        return reply({ error: "GitHub could not queue build; check Worker/GitHub configuration" }, 502, headers);
      return reply({ queued: true, message: "Static SEO rebuild queued" }, 202, headers);
    } catch (_) {
      return reply({ error: "Trigger request failed; check Worker logs" }, 502, headers);
    }
  }
};
