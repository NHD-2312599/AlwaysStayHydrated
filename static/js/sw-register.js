(function () {
  if (!('serviceWorker' in navigator)) return;

  const swUrl = `/sw.js?v=${Date.now()}`;

  // Xoá tất cả ServiceWorker cũ trước
  navigator.serviceWorker.getRegistrations().then((regs) => {
    Promise.all(regs.map(reg => reg.unregister()));
  }).then(() => {
    // Rồi mới register cái mới
    navigator.serviceWorker.register(swUrl).then((reg) => {
      reg.update();
      // Nếu có ServiceWorker mới chờ, ép nó activate ngay
      if (reg.waiting) {
        reg.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    }).catch((err) => console.error('SW registration failed', err));
  });
})();
