let deferredPrompt;

window.addEventListener("beforeinstallprompt", e => {
  e.preventDefault();
  deferredPrompt = e;

  // Inject styles
  const style = document.createElement("style");
  style.textContent = `
    @keyframes slideUp {
      from { transform: translateY(120px); opacity: 0; }
      to   { transform: translateY(0);    opacity: 1; }
    }
    @keyframes pulse-ring {
      0%   { box-shadow: 0 0 0 0 rgba(52, 168, 83, 0.4); }
      70%  { box-shadow: 0 0 0 12px rgba(52, 168, 83, 0); }
      100% { box-shadow: 0 0 0 0 rgba(52, 168, 83, 0); }
    }
    #pwa-install-card {
      position: fixed;
      bottom: 24px;
      right: 20px;
      z-index: 99999;
      width: 300px;
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.08);
      padding: 18px 20px 16px;
      animation: slideUp 0.45s cubic-bezier(0.34,1.56,0.64,1) both;
      font-family: 'Segoe UI', sans-serif;
      border: 1.5px solid rgba(52,168,83,0.15);
    }
    #pwa-install-card .pwa-top {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
    }
    #pwa-install-card .pwa-icon {
      width: 46px;
      height: 46px;
      background: linear-gradient(135deg, #2d6a4f, #52b788);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      flex-shrink: 0;
    }
    #pwa-install-card .pwa-title {
      font-size: 14px;
      font-weight: 700;
      color: #1a3c2e;
      margin: 0 0 2px;
    }
    #pwa-install-card .pwa-subtitle {
      font-size: 12px;
      color: #6b7280;
      margin: 0;
      line-height: 1.4;
    }
    #pwa-install-card .pwa-desc {
      font-size: 12.5px;
      color: #4b5563;
      margin: 0 0 14px;
      line-height: 1.5;
      background: #f0faf4;
      border-radius: 10px;
      padding: 8px 10px;
    }
    #pwa-install-card .pwa-actions {
      display: flex;
      gap: 8px;
    }
    #pwa-install-card .pwa-btn-install {
      flex: 1;
      background: linear-gradient(135deg, #2d6a4f, #40916c);
      color: #fff;
      border: none;
      border-radius: 12px;
      padding: 10px 0;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      animation: pulse-ring 2s ease-out infinite;
      transition: transform 0.15s, opacity 0.15s;
      letter-spacing: 0.3px;
    }
    #pwa-install-card .pwa-btn-install:hover {
      transform: translateY(-1px);
      opacity: 0.92;
    }
    #pwa-install-card .pwa-btn-dismiss {
      background: #f3f4f6;
      color: #6b7280;
      border: none;
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 13px;
      cursor: pointer;
      transition: background 0.15s;
    }
    #pwa-install-card .pwa-btn-dismiss:hover {
      background: #e5e7eb;
    }
    #pwa-install-card .pwa-close {
      position: absolute;
      top: 10px;
      right: 12px;
      background: none;
      border: none;
      font-size: 16px;
      color: #9ca3af;
      cursor: pointer;
      line-height: 1;
      padding: 2px;
    }
  `;
  document.head.appendChild(style);

  // Build card
  const card = document.createElement("div");
  card.id = "pwa-install-card";
  card.innerHTML = `
    <button class="pwa-close" id="pwa-close-btn" title="Đóng">✕</button>
    <div class="pwa-top">
      <div class="pwa-icon">💧</div>
      <div>
        <p class="pwa-title">Always Stay Hydrated</p>
        <p class="pwa-subtitle">Ứng dụng học Kinh Thánh</p>
      </div>
    </div>
    <p class="pwa-desc">📲 Bạn có muốn tải ứng dụng về máy không? Truy cập nhanh hơn, dùng được offline!</p>
    <div class="pwa-actions">
      <button class="pwa-btn-install" id="pwa-install-btn">⬇ Cài ngay</button>
      <button class="pwa-btn-dismiss" id="pwa-dismiss-btn">Để sau</button>
    </div>
  `;
  document.body.appendChild(card);

  document.getElementById("pwa-install-btn").onclick = async () => {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    card.remove();
    deferredPrompt = null;
  };

  const dismiss = () => {
    card.style.transition = "transform 0.3s ease, opacity 0.3s ease";
    card.style.transform = "translateY(120px)";
    card.style.opacity = "0";
    setTimeout(() => card.remove(), 320);
  };

  document.getElementById("pwa-dismiss-btn").onclick = dismiss;
  document.getElementById("pwa-close-btn").onclick = dismiss;
});
