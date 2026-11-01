// Service worker: laat de app zonder internet werken.
// Verhoog VERSIE als je index.html aanpast, dan krijgen telefoons de nieuwe versie.
const VERSIE = 'rantsoen-v7';
const KERN = [
  './',
  './index.html',
  './manifest.webmanifest',
  './prijzen.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSIE).then(c => c.addAll(KERN)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== VERSIE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function netwerkEerst(req) {
  return fetch(req).then(resp => {
    if (resp && resp.ok) { const kopie = resp.clone(); caches.open(VERSIE).then(c => c.put(req, kopie)); }
    return resp;
  }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match('./index.html')));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // App zelf en prijzen: eerst internet (nieuwste versie), anders uit de opslag
  if (req.mode === 'navigate' || (url.origin === location.origin && url.pathname.endsWith('/prijzen.json'))) {
    e.respondWith(netwerkEerst(req));
    return;
  }
  // Overige eigen bestanden en lettertypen: eerst uit de opslag
  if (url.origin === location.origin || url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(resp => {
      if (resp && (resp.ok || resp.type === 'opaque')) { const kopie = resp.clone(); caches.open(VERSIE).then(c => c.put(req, kopie)); }
      return resp;
    })));
  }
});
