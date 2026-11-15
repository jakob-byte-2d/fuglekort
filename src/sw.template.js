// Hagefugler – offline-støtte for den frittstående appen.
// build.py setter versjonen ut fra innholdet, så telefonene henter alt på nytt etter hver endring.
const CACHE = 'hagefugler-v1';
const ASSETS = __ASSETS__;

self.addEventListener('install', event => {
  // { cache: 'reload' }: straight from the network, not the browser's own cache, so a new version never keeps an old card picture
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS.map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Kortbilder, fonter og app-filer: fra cache først, og oppdatert i bakgrunnen. Bare samme nettsted (Supabase går utenom).
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  event.respondWith(
    caches.open(CACHE).then(async cache => {
      const hit = await cache.match(req, { ignoreSearch: true });
      const net = fetch(req).then(res => {
        if (res && res.ok) cache.put(req, res.clone());
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});

// Varsler (push fra send-varsler i Supabase): vis varselet. Et trykk åpner appen, i fanen Telling eller på tavla.
self.addEventListener('push', event => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) { d = { tekst: event.data ? event.data.text() : '' }; }
  event.waitUntil(self.registration.showNotification(d.tittel || 'Hagefugler', {
    body: d.tekst || '', icon: 'icons/icon-192.png', tag: d.tag || undefined, lang: 'nb', data: { url: d.url || './' },
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = new URL((event.notification.data && event.notification.data.url) || './', self.registration.scope);
  const vis = url.searchParams.get('vis');
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    const c = cs.find(x => x.url.startsWith(self.registration.scope));
    if (c) { if (vis) c.postMessage({ type: 'vis', vis }); return c.focus(); }
    return self.clients.openWindow(url.href);
  }));
});
