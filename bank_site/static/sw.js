const CACHE_NAME = 'skybridge-v2.0.1';
const STATIC_ASSETS = [
  '/',
  '/static/img/blue.png',
  '/static/css/dash.css',
  '/static/js/main.js',
  '/static/manifest.json',
  '/offline/'
];

// Cache strategies
const STRATEGIES = {
  STATIC: 'static',
  DYNAMIC: 'dynamic',
  NETWORK_FIRST: 'network-first'
};

// URL patterns and their caching strategies
const ROUTE_PATTERNS = {
  '/static/': STRATEGIES.STATIC,
  '/media/': STRATEGIES.DYNAMIC,
  '/api/': STRATEGIES.NETWORK_FIRST,
  '/dashboard': STRATEGIES.NETWORK_FIRST,
  '/transfer': STRATEGIES.NETWORK_FIRST,
  '/profile': STRATEGIES.NETWORK_FIRST
};

self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    Promise.all([
      // Pre-cache critical assets
      caches.open(CACHE_NAME).then(cache => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS).catch(error => {
          console.warn('[Service Worker] Failed to cache some assets:', error);
        });
      }),
      
      // Create offline page cache
      caches.open(`${CACHE_NAME}-offline`).then(cache => {
        return cache.add('/offline/').catch(() => {
          console.log('[Service Worker] No offline page available');
        });
      })
    ])
  );
  
  // Force activation
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (![CACHE_NAME, `${CACHE_NAME}-offline`].includes(cacheName)) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Claim all clients immediately
      self.clients.claim()
    ])
  );
});

// Determine caching strategy for a request
function getCacheStrategy(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // Check if it's a static file
  if (path.startsWith('/static/') || 
      path.match(/\.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$/i)) {
    return STRATEGIES.STATIC;
  }
  
  // Check if it's an API call
  if (path.startsWith('/api/')) {
    return STRATEGIES.NETWORK_FIRST;
  }
  
  // Default to network-first for HTML pages
  if (request.headers.get('accept')?.includes('text/html')) {
    return STRATEGIES.NETWORK_FIRST;
  }
  
  return STRATEGIES.DYNAMIC;
}

// Cache-first strategy for static assets
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    console.log('[Service Worker] Serving from cache:', request.url);
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone()).catch(error => {
        console.warn('[Service Worker] Failed to cache response:', error);
      });
    }
    
    return networkResponse;
  } catch (error) {
    console.warn('[Service Worker] Network failed, no cache available:', request.url);
    
    // Return appropriate fallback
    if (request.destination === 'image') {
      return caches.match('/static/img/blue.png');
    }
    
    if (request.headers.get('accept')?.includes('text/html')) {
      return caches.match('/offline/');
    }
    
    return new Response('Offline', {
      status: 503,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

// Network-first strategy for dynamic content
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.status === 200) {
      // Cache successful responses
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone()).catch(error => {
        console.warn('[Service Worker] Failed to cache response:', error);
      });
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // For navigation requests, return offline page
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match('/offline/');
      if (offlinePage) {
        return offlinePage;
      }
      
      return new Response(
        '<h1>Offline</h1><p>Please check your internet connection.</p>',
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'text/html' }
        }
      );
    }
    
    return new Response('Network error', {
      status: 408,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

// Dynamic caching strategy
async function dynamicCache(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.status === 200) {
      const cache = await caches.open(`${CACHE_NAME}-dynamic`);
      cache.put(request, networkResponse.clone()).catch(error => {
        console.warn('[Service Worker] Failed to cache dynamic response:', error);
      });
    }
    
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    return cachedResponse || networkResponse;
  }
}

self.addEventListener('fetch', event => {
  const { request } = event;
  
  // Skip non-GET requests and certain URLs
  if (request.method !== 'GET' ||
      request.url.startsWith('chrome-extension://') ||
      request.url.includes('browser-sync') ||
      request.url.includes('hot-update')) {
    return;
  }
  
  // Skip Django admin and debug toolbar
  if (request.url.includes('/admin/') || 
      request.url.includes('/__debug__/')) {
    return;
  }
  
  const strategy = getCacheStrategy(request);
  
  switch (strategy) {
    case STRATEGIES.STATIC:
      event.respondWith(cacheFirst(request));
      break;
      
    case STRATEGIES.NETWORK_FIRST:
      event.respondWith(networkFirst(request));
      break;
      
    case STRATEGIES.DYNAMIC:
      event.respondWith(dynamicCache(request));
      break;
      
    default:
      event.respondWith(fetch(request));
  }
});

// Periodic cache cleanup
async function cleanupOldCacheEntries() {
  const cache = await caches.open(`${CACHE_NAME}-dynamic`);
  const keys = await cache.keys();
  const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
  
  for (const request of keys) {
    const response = await cache.match(request);
    if (response) {
      const dateHeader = response.headers.get('date');
      if (dateHeader) {
        const date = new Date(dateHeader).getTime();
        if (date < weekAgo) {
          await cache.delete(request);
        }
      }
    }
  }
}

// Periodic sync (every 24 hours)
self.addEventListener('periodicsync', event => {
  if (event.tag === 'cleanup-cache') {
    event.waitUntil(cleanupOldCacheEntries());
  }
});

// Background sync for failed requests
self.addEventListener('sync', event => {
  if (event.tag === 'sync-failed-requests') {
    console.log('[Service Worker] Background sync triggered');
    event.waitUntil(syncFailedRequests());
  }
});

async function syncFailedRequests() {
  // Implement failed request retry logic here
  // This could queue failed API calls and retry them
}

// Push notifications
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'New update from SkyBridge Bank',
    icon: '/static/img/blue.png',
    badge: '/static/img/blue.png',
    image: '/static/img/blue.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/static/img/blue.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/img/blue.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('SkyBridge Bank', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(windowClients => {
        // Check if there's already a window/tab open
        for (const client of windowClients) {
          if (client.url.includes('skybridgefinance.online') && 'focus' in client) {
            return client.focus();
          }
        }
        
        // If not, open a new window
        if (clients.openWindow) {
          return clients.openWindow(event.notification.data.url || '/');
        }
      })
    );
  }
});

// Handle messages from the client
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(CACHE_NAME);
    caches.delete(`${CACHE_NAME}-dynamic`);
  }
});