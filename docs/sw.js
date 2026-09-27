// Hagefugler Oslo – offline-støtte for den frittstående appen.
// Øk versjonen når kortbildene eller appen endres, så hentes alt på nytt.
const CACHE = 'hagefugler-oslo-v1';
const ASSETS = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "sprites/photos.webp",
  "sprites/cards.webp",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/apple-touch-icon.png",
  "cards/001.webp",
  "cards/002.webp",
  "cards/003.webp",
  "cards/004.webp",
  "cards/005.webp",
  "cards/006.webp",
  "cards/007.webp",
  "cards/008.webp",
  "cards/009.webp",
  "cards/010.webp",
  "cards/011.webp",
  "cards/012.webp",
  "cards/013.webp",
  "cards/014.webp",
  "cards/015.webp",
  "cards/016.webp",
  "cards/017.webp",
  "cards/018.webp",
  "cards/019.webp",
  "cards/020.webp",
  "cards/021.webp",
  "cards/022.webp",
  "cards/023.webp",
  "cards/024.webp",
  "cards/025.webp",
  "cards/026.webp",
  "cards/027.webp",
  "cards/028.webp",
  "cards/029.webp",
  "cards/030.webp",
  "cards/031.webp",
  "cards/032.webp",
  "cards/033.webp",
  "cards/034.webp",
  "cards/035.webp",
  "cards/036.webp",
  "cards/037.webp",
  "cards/038.webp",
  "cards/039.webp",
  "cards/040.webp",
  "cards/041.webp",
  "cards/042.webp",
  "cards/043.webp",
  "cards/044.webp",
  "cards/045.webp",
  "cards/046.webp",
  "cards/047.webp",
  "cards/048.webp",
  "cards/049.webp",
  "cards/050.webp",
  "cards/051.webp",
  "cards/052.webp",
  "cards/053.webp",
  "cards/054.webp",
  "cards/055.webp",
  "cards/056.webp",
  "cards/057.webp",
  "cards/058.webp",
  "cards/059.webp",
  "cards/060.webp"
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
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
