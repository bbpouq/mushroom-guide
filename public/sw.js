/* 拾菌记 MycoTrail service worker: cache the app shell for offline use */
const CACHE = "mushroom-guide-v43";
// Photos and the 3D library live in their own cache that survives releases, so photos downloaded for offline use are
// not lost on every update. Bump the number only when existing photo files are replaced by different pictures.
const MEDIA = "mushroom-guide-media-1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icon.svg", "./favicon-32.png", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== MEDIA).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  // pages: network first so updates arrive, cached copy when offline
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put("./index.html", copy)); return r; })
      .catch(() => caches.match("./index.html")));
    return;
  }
  // Google Fonts: serve cached, refresh in background
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(CACHE).then(c => c.match(req).then(hit => {
      const net = fetch(req).then(r => { c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  // example photos and the 3D library: cache each the first time it is used, so it is there offline later
  if (url.origin === self.location.origin && (url.pathname.includes("/photos/") || url.pathname.includes("/vendor/"))) {
    e.respondWith(caches.open(MEDIA).then(c => c.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }))));
    return;
  }
  // own files: cache first
  if (url.origin === self.location.origin) e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
