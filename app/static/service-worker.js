// Service Worker版本号
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `card-game-${CACHE_VERSION}`;

// 需要缓存的静态资源
const STATIC_CACHE_URLS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json'
];

// 需要缓存的页面路由（动态内容）
const DYNAMIC_CACHE_URLS = [
  '/auth/login',
  '/auth/register',
  '/cards/',
  '/gacha/',
  '/battle/'
];

// 安装事件：缓存静态资源
self.addEventListener('install', (event) => {
  console.log('[Service Worker] 安装中...', CACHE_VERSION);

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] 缓存静态资源');
      return cache.addAll(STATIC_CACHE_URLS);
    }).then(() => {
      // 强制激活新的Service Worker
      return self.skipWaiting();
    })
  );
});

// 激活事件：清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] 激活中...', CACHE_VERSION);

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] 删除旧缓存:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // 立即控制所有页面
      return self.clients.claim();
    })
  );
});

// Fetch事件：网络请求拦截
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }

  // API请求：网络优先，失败时使用缓存
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/gacha/pull') ||
      url.pathname.startsWith('/battle/start')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // 克隆响应，一份给缓存，一份给用户
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // 网络失败，尝试从缓存获取
          return caches.match(request);
        })
    );
    return;
  }

  // 静态资源和页面：缓存优先，失败时使用网络
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // 从缓存返回，同时在后台更新缓存
        fetch(request).then((response) => {
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, response);
          });
        }).catch(() => {
          // 网络请求失败，忽略
        });
        return cachedResponse;
      }

      // 缓存中没有，从网络获取
      return fetch(request).then((response) => {
        // 只缓存成功的GET请求
        if (request.method === 'GET' && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      }).catch((error) => {
        console.error('[Service Worker] Fetch失败:', error);

        // 如果是页面请求，返回离线页面
        if (request.mode === 'navigate') {
          return caches.match('/');
        }

        throw error;
      });
    })
  );
});

// 消息事件：接收来自页面的消息
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }
});

// 推送通知事件（未来扩展）
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || '您有新的通知',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png',
      vibrate: [200, 100, 200],
      data: {
        url: data.url || '/'
      }
    };

    event.waitUntil(
      self.registration.showNotification(data.title || '卡牌游戏', options)
    );
  }
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

console.log('[Service Worker] 已加载', CACHE_VERSION);
