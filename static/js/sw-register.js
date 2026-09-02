(function () {
  if (!('serviceWorker' in navigator)) return;

  // Xoá tất cả ServiceWorker cũ trước
  navigator.serviceWorker.getRegistrations().then((regs) => {
    Promise.all(regs.map(reg => reg.unregister()));
  }).then(() => {
    // Rồi mới register cái mới
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      reg.update();
      // Nếu có ServiceWorker mới chờ, ép nó activate ngay
      if (reg.waiting) {
        reg.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    }).catch((err) => console.error('SW registration failed', err));
  });
})();
