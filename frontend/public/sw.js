const VERSION = 'v4'
const APP_SHELL_CACHE = `app-shell-${VERSION}`
const RUNTIME_CACHE = `runtime-${VERSION}`
const MAP_CACHE = `map-${VERSION}`
const APP_SHELL_URLS = [
  '/',
  '/impressum',
  '/datenschutz',
  '/site.webmanifest',
  '/favicon.ico',
  '/icons/apple-touch-icon.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/icon-512-maskable.png',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => cache.addAll(APP_SHELL_URLS)),
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => ![APP_SHELL_CACHE, RUNTIME_CACHE, MAP_CACHE].includes(key))
        .map((key) => caches.delete(key)),
    )),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event

  if (request.method !== 'GET') {
    return
  }

  const url = new URL(request.url)

  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request))
    return
  }

  if (url.origin !== self.location.origin) {
    return
  }

  if (isMapRequest(url)) {
    event.respondWith(staleWhileRevalidate(request, MAP_CACHE))
    return
  }

  event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE))
})

async function handleNavigationRequest(request) {
  try {
    const response = await fetch(request)
    const cache = await caches.open(APP_SHELL_CACHE)
    cache.put(request, response.clone())
    return response
  } catch {
    const cachedResponse = await caches.match(request)
    return cachedResponse || caches.match('/')
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName)
  const cachedResponse = await cache.match(request)

  const networkPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone())
      }
      return response
    })
    .catch(() => cachedResponse)

  return cachedResponse || networkPromise
}

function isMapRequest(url) {
  return url.pathname.startsWith('/gosm') || url.pathname.startsWith('/api')
}
