# Secure Publish Trigger (Admin Panel integration)

The Admin Panel now calls the secure Worker after a successful Firestore publish. The Worker must be deployed and its URL configured before automatic dispatch can work. Draft saves do not trigger a build.

## Configure Cloudflare Worker

1. Create a Cloudflare Worker and paste `cloudflare-worker/worker.js`.
2. Set Worker variables/secrets:
   - `FIREBASE_API_KEY`: existing Firebase Web API key.
   - `FIREBASE_ADMIN_UID`: authorized admin UID from Firebase Authentication.
   - `GITHUB_TOKEN`: fine-grained token limited to repository `examdarpanoffical/examdarpan-seo-ai`, with Actions read/write permission.
   - `ALLOWED_ORIGIN`: `https://examdarpan.in`.
3. Deploy Worker and copy its HTTPS URL. Keep `GITHUB_TOKEN` in Worker secrets only.

## Configure the Admin Panel (after Worker deploy)

After deploying the Worker, add this line to `public/firebase-config.js` (replace the example with the exact deployed Worker URL):

```js
window.EXAMDARPAN_PUBLISH_TRIGGER_URL = 'https://YOUR-WORKER-NAME.YOUR-SUBDOMAIN.workers.dev';
```

Do not put `GITHUB_TOKEN` in `firebase-config.js` or any browser file. The Admin Panel obtains the current Firebase ID token and sends it to the Worker; the Worker validates the Firebase identity against `FIREBASE_ADMIN_UID` before dispatching GitHub Actions.

The Admin Panel's `save(status)` already invokes the secure trigger after Firestore save for published posts and displays a distinct message if triggering fails.

## Manual test

The helper has already been added to `public/admin/dashboard.js`; this is the request it performs:

```js
const SEO_TRIGGER_URL = 'https://YOUR-WORKER-NAME.YOUR-SUBDOMAIN.workers.dev';

async function triggerStaticSeoBuild() {
  const user = auth.currentUser;
  if (!user) throw new Error('Admin login expired. Sign in again.');
  const token = await user.getIdToken();
  const response = await fetch(SEO_TRIGGER_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ reason: 'admin-publish' })
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || result.queued !== true)
    throw new Error(result.error || 'Static SEO rebuild could not be queued.');
  return result;
}
```

The code triggers only after successful Firestore save when `status === 'published'`. If trigger fails, the message explicitly says the article is saved but the static build was not queued. Drafts do not trigger builds.

## Notes

- This does not deploy itself: Cloudflare account settings and secrets require the site owner.
- Test new publication and edits of existing published articles before enabling for regular use.
- The existing GitHub workflow already supports `workflow_dispatch` and deploys Hosting.
- Do not promise an exact three-minute completion; GitHub queue and Firebase Hosting deployment can vary.
- Every rebuild reads published posts. Static visitor page requests do not need a Firestore read per article view, but frequent rebuilds may use more reads than the current hourly schedule.
