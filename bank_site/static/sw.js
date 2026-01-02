const CACHE_NAME = 'skybridge-v1';
const STATIC_ASSETS = [
  '/',
  '/static/img/logo-180x180.svg',
  '/static/img/splash-512x512.svg',
  '/manifest.json',
  '/favicon.ico',
  '/static/css/main.css',
  '/static/js/main.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Caching static assets:', STATIC_ASSETS);
      return cache.addAll(STATIC_ASSETS).catch(error => {
        console.warn('Failed to cache some assets:', error);
      });
    })
  );
  // Skip waiting to activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  // Clean up old caches
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control of all clients
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Skip non-GET requests and browser extensions
  if (event.request.method !== 'GET' || 
      event.request.url.startsWith('chrome-extension://') ||
      event.request.url.includes('browser-sync')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      // Return cached response if available
      if (cachedResponse) {
        return cachedResponse;
      }

      // Otherwise fetch from network
      return fetch(event.request).then(networkResponse => {
        // Don't cache non-successful responses or opaque responses
        if (!networkResponse || networkResponse.status !== 200 || 
            networkResponse.type === 'opaque') {
          return networkResponse;
        }

        // Clone response to cache and return
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseToCache).catch(error => {
            console.warn('Failed to cache:', event.request.url, error);
          });
        });

        return networkResponse;
      }).catch(error => {
        console.warn('Network fetch failed:', event.request.url, error);
        
        // For navigation requests, return the cached homepage
        if (event.request.mode === 'navigate') {
          return caches.match('/').then(homepageResponse => {
            return homepageResponse || new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({ 'Content-Type': 'text/html' })
            });
          });
        }
        
        // For other requests, return a fallback
        if (event.request.destination === 'image') {
          return caches.match('/static/img/logo-180x180.svg');
        }
        
        return new Response('Network error', {
          status: 408,
          statusText: 'Network request failed'
        });
      });
    })
  );
});

// Handle background sync (optional)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

// Handle push notifications (optional)
self.addEventListener('push', event => {
  const options = {
    body: event.data?.text() || 'New update from SkyBridge Bank',
    icon: '/static/img/logo-180x180.svg',
    badge: '/static/img/logo-180x180.svg',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'Explore',
        icon: '/static/img/logo-180x180.svg'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/img/logo-180x180.svg'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('SkyBridge Bank', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('https://skybridgefinance.online/')
    );
  } else {
    event.waitUntil(
      clients.openWindow('https://skybridgefinance.online/')
    );
  }
});

// Helper function for background sync
async function syncData() {
  // Implement your data synchronization logic here
  console.log('Background sync triggered');
}