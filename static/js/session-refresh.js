/** Xóa cache PWA sau đăng xuất / đổi tài khoản */
async function clearAshCaches() {
  if ('caches' in window) {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => caches.delete(key)));
  }
  if ('serviceWorker' in navigator) {
    const reg = await navigator.serviceWorker.ready.catch(() => null);
    reg?.active?.postMessage({ type: 'CLEAR_CACHE' });
    await reg?.update();
  }
}

/** Gọi callback khi tab hiện lại hoặc trang restore từ bfcache */
function onSessionVisible(callback) {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') callback();
  });
  window.addEventListener('pageshow', (e) => {
    if (e.persisted) callback();
  });
}

/** fetch API theo session hiện tại — không dùng cache trình duyệt */
function apiFetch(url, options = {}) {
  return fetch(url, {
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { Accept: 'application/json', 'Cache-Control': 'no-cache', ...(options.headers || {}) },
    ...options,
  });
}
