const CACHE_NAME = '1v1fighter-v3';

self.addEventListener('install', (event) => {
  // Take over immediately — don't wait for old tabs to close
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Delete every old cache
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  // Start controlling all open tabs right away
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Network-first for EVERYTHING.
  // The cache is only used as an offline fallback.
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache a copy so the app works offline next time
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
