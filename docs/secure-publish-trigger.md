# Secure Publish Trigger (staged)

This adds the secure Worker source and setup guide only. It does not modify the live Admin Panel or Firebase Hosting configuration. The Worker must be deployed and its URL known before connecting the browser code.

## Configure Cloudflare Worker

1. Create a Cloudflare Worker and paste `cloudflare-worker/worker.js`.
2. Set Worker variables/secrets:
   - `FIREBASE_API_KEY`: existing Firebase Web API key.
   - `FIREBASE_ADMIN_UID`: authorized admin UID from Firebase Authentication.
   - `GITHUB_TOKEN`: fine-grained token limited to repository `examdarpanoffical/examdarpan-seo-ai`, with Actions read/write permission.
   - `ALLOWED_ORIGIN`: `https://examdarpan.in`.
3. Deploy Worker and copy its HTTPS URL. Keep `GITHUB_TOKEN` in Worker secrets only.

## Admin Panel connection (after Worker deploy)

Add a helper to `public/admin/dashboard.js` and replace the URL with the actual Worker URL:

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

In the existing `save(status)`, call `await triggerStaticSeoBuild()` only after a successful Firestore save when `status === 'published'`. If trigger fails, report that the article saved but static rebuild was not queued. Do not trigger for drafts.

## Notes

- This does not deploy itself: Cloudflare account settings and secrets require the site owner.
- Test new publication and edits of existing published articles before enabling for regular use.
- The existing GitHub workflow already supports `workflow_dispatch` and deploys Hosting.
- Do not promise an exact three-minute completion; GitHub queue and Firebase Hosting deployment can vary.
- Every rebuild reads published posts. Static visitor page requests do not need a Firestore read per article view, but frequent rebuilds may use more reads than the current hourly schedule.
