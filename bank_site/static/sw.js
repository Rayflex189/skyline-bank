const CACHE_NAME = 'skybridge-v2.0.1';
const STATIC_ASSETS = [
  '/',
  // Original and all resized icons
  '/static/img/blue.png',
  '/static/img/blue-16x16.png',
  '/static/img/blue-32x32.png',
  '/static/img/blue-72x72.png',
  '/static/img/blue-96x96.png',
  '/static/img/blue-128x128.png',
  '/static/img/blue-144x144.png',
  '/static/img/blue-152x152.png',
  '/static/img/blue-180x180.png',
  '/static/img/blue-192x192.png',
  '/static/img/blue-384x384.png',
  '/static/img/blue-512x512.png',
  '/static/img/favicon.ico',
  '/static/img/blue-screenshot.png',
  // Other assets
  '/static/css/dash.css',
  '/static/js/main.js',
  '/static/manifest.json',
  '/offline/'
];

// Update fallback image to use standard 192x192 size
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
    
    // Return appropriate fallback - use 192x192 for image fallback
    if (request.destination === 'image') {
      return caches.match('/static/img/blue-192x192.png');
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

// Update push notifications to use 192x192 icon
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'New update from SkyBridge Bank',
    icon: '/static/img/blue-192x192.png',  // Updated
    badge: '/static/img/blue-192x192.png',  // Updated
    image: '/static/img/blue-192x192.png',  // Updated
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/static/img/blue-96x96.png'  // Updated
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/img/blue-96x96.png'  // Updated
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('SkyBridge Bank', options)
  );
});