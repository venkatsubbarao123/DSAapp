/**
 * DSAapp Production Service Worker
 * Phase 9: Progressive Web App (PWA) Foundation
 *
 * CRITICAL SECURITY INVARIANTS:
 * 1. Network-Only for ALL /api/* requests, /health, auth tokens, payments, code executions, and admin operations.
 * 2. NEVER cache authentication tokens, credentials, sensitive submission source codes, or payments data.
 * 3. Cache-First for static assets (scripts, stylesheets, fonts, icons).
 * 4. Stale-While-Revalidate for app shell navigation with graceful offline fallback.
 */

const CACHE_NAME = 'dsaapp-shell-v1';

// Static assets to precache during service worker installation
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

// 1. Installation: Precache core shell assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// 2. Activation: Clean up stale cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch interceptor
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Non-GET requests (POST, PUT, PATCH, DELETE) -> Network Only
  if (request.method !== 'GET') {
    return;
  }

  // SECURITY RULE: Never intercept or cache API or health check endpoints
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/health') ||
    url.pathname.includes('/auth/') ||
    url.pathname.includes('/payments/') ||
    url.pathname.includes('/judge/') ||
    url.pathname.includes('/admin/')
  ) {
    // Network-Only: standard browser fetch
    return;
  }

  // Navigation requests (HTML pages): Network-first with cache fallback (offline support)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() => {
          // Offline fallback: serve cached shell
          return caches.match(request).then((cached) => {
            return cached || caches.match('/index.html');
          });
        })
    );
    return;
  }

  // Static Assets (JS, CSS, fonts, SVG, PNG): Cache-First with Network fallback
  if (
    url.pathname.match(/\.(js|css|woff2?|png|jpg|jpeg|svg|ico)$/) ||
    url.pathname.startsWith('/assets/')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Default fallback: Network with cache fallback
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

// 4. Message Handler (for manual updates e.g. skipWaiting)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
