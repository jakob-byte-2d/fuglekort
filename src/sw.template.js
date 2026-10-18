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

// Kortbilder og app-filer: fra cache først. Google Fonts: cache, og oppdater i bakgrunnen.
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (url.origin !== location.origin && !isFont) return;
  event.respondWith(
    caches.open(CACHE).then(async cache => {
      const hit = await cache.match(req, { ignoreSearch: !isFont });
      const net = fetch(req).then(res => {
        if (res && (res.ok || res.type === 'opaque')) cache.put(req, res.clone());
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
