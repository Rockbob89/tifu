const VERSION = 'v7';
const SHELL_CACHE = `tifu-shell-${VERSION}`;
const API_CACHE = `tifu-api-${VERSION}`;

const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './changelog.json',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './apple-touch-icon.png',
];

const API_HOST = 'tifu-proxy.tifu-proxy.workers.dev';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      cache.addAll(SHELL_ASSETS.map((url) => new Request(url, { cache: 'reload' })))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== SHELL_CACHE && k !== API_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  if (url.host === API_HOST) {
    event.respondWith(networkFirst(req, API_CACHE));
    return;
  }

  if (url.origin === self.location.origin) {
    if (isHtml(req, url)) {
      event.respondWith(staleWhileRevalidate(req, SHELL_CACHE));
    } else {
      event.respondWith(cacheFirst(req, SHELL_CACHE));
    }
  }
});

function isHtml(req, url) {
  if (url.pathname === '/' || url.pathname.endsWith('.html')) return true;
  if (url.pathname.endsWith('changelog.json')) return true;
  const accept = req.headers.get('accept') || '';
  return accept.includes('text/html');
}

async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req)
    .then((res) => {
      if (res.ok) cache.put(req, res.clone());
      return res;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const cached = await cache.match(req);
    if (cached) return cached;
    throw err;
  }
}
