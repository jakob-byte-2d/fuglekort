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
