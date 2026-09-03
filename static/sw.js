const CACHE_NAME = 'ash-v6';
const ASSETS = [
  '/offline.html',
  '/manifest.json',
  '/static/manifest.json',
  '/static/css/mobile-responsive.css',
  '/static/js/pwa-install.js',
  '/static/js/sw-register.js',
  '/static/js/session-refresh.js',
  '/static/pictures/Logo_White.png'
];

/** Trang có dữ liệu theo session — không cache HTML */
const AUTH_HTML_PREFIXES = [
  '/home',
  '/flashcard',
  '/exam_library',
  '/exam/',
];

function getPath(url) {
  try {
    return new URL(url).pathname;
  } catch {
    return '';
  }
}

function isApiRequest(url) {
  return getPath(url).startsWith('/api/');
}

function isAuthHtmlRequest(url) {
  const path = getPath(url);
  return AUTH_HTML_PREFIXES.some(
    (p) => path === p || path.startsWith(p)
  );
}

function networkOnly(request) {
  return fetch(new Request(request, { cache: 'no-store' }));
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
      )
      .then(() => self.clients.claim())
  );
  // Ép ServiceWorker mới activate ngay, không đợi page reload
  self.skipWaiting();
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data?.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
    );
  }
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (isApiRequest(request.url)) {
    event.respondWith(networkOnly(request));
    return;
  }

  if (isAuthHtmlRequest(request.url)) {
    event.respondWith(networkOnly(request));
    return;
  }

  if (
    request.mode === 'navigate' ||
    (request.method === 'GET' && request.headers.get('accept')?.includes('text/html'))
  ) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok && !isAuthHtmlRequest(request.url)) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match('/offline.html'))
        )
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(request).then((response) => {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          if (request.url.startsWith(self.location.origin)) {
            cache.put(request, responseClone);
          }
        });
        return response;
      });
    })
  );
});
