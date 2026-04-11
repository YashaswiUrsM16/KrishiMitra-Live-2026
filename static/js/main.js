// ── PAGE LOAD ANIMATIONS ──────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateCards();
  initNotifications();
  initScrollTop();
  highlightNav();
});

function animateCards() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity    = '1';
          entry.target.style.transform  = 'translateY(0)';
        }, i * 80);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card, .stat-card, .price-card, .scheme-card, .tip-card, .forecast-card')
    .forEach(el => {
      el.style.opacity   = '0';
      el.style.transform = 'translateY(24px)';
      el.style.transition= 'opacity 0.4s ease, transform 0.4s ease';
      observer.observe(el);
    });
}

// ── NOTIFICATIONS ─────────────────────────────────
function initNotifications() {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
  `;
  document.body.appendChild(container);
}

function showToast(message, type = 'success', duration = 3500) {
  const colors = {
    success: { bg: '#d8f3dc', border: '#2d6a4f', text: '#1b4332', icon: '✅' },
    error:   { bg: '#ffe0e0', border: '#e63946', text: '#7d0000', icon: '❌' },
    info:    { bg: '#ddf4f0', border: '#40916c', text: '#1b4332', icon: 'ℹ️'  },
    warning: { bg: '#fff3cd', border: '#f4a261', text: '#856404', icon: '⚠️' },
  };
  const c     = colors[type] || colors.success;
  const toast = document.createElement('div');
  toast.style.cssText = `
    background: ${c.bg};
    border-left: 4px solid ${c.border};
    color: ${c.text};
    padding: 14px 20px;
    border-radius: 12px;
    font-family: 'Poppins', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 280px;
    max-width: 360px;
    opacity: 0;
    transform: translateX(40px);
    transition: all 0.3s ease;
    cursor: pointer;
  `;
  toast.innerHTML = `<span>${c.icon}</span><span>${message}</span>`;
  toast.onclick   = () => removeToast(toast);

  document.getElementById('toast-container').appendChild(toast);
  requestAnimationFrame(() => {
    toast.style.opacity   = '1';
    toast.style.transform = 'translateX(0)';
  });
  setTimeout(() => removeToast(toast), duration);
}

function removeToast(toast) {
  toast.style.opacity   = '0';
  toast.style.transform = 'translateX(40px)';
  setTimeout(() => toast.remove(), 300);
}

// ── SCROLL TO TOP ─────────────────────────────────
function initScrollTop() {
  const btn = document.createElement('button');
  btn.id    = 'scrollTopBtn';
  btn.innerHTML = '↑';
  btn.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #2d6a4f;
    color: white;
    border: none;
    font-size: 1.3rem;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(45,106,79,0.3);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 999;
    transition: all 0.2s;
    font-family: sans-serif;
  `;
  btn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
  btn.onmouseover = () => btn.style.background = '#1b4332';
  btn.onmouseout  = () => btn.style.background = '#2d6a4f';
  document.body.appendChild(btn);

  window.addEventListener('scroll', () => {
    btn.style.display = window.scrollY > 300 ? 'flex' : 'none';
  });
}

// ── ACTIVE NAV HIGHLIGHT ──────────────────────────
function highlightNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-item').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}

// ── LOADING BUTTON ────────────────────────────────
function setLoading(btn, loading, text = 'Loading...') {
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span style="display:inline-block;animation:spin 0.8s linear infinite">⟳</span> ${text}`;
    btn.disabled  = true;
  } else {
    btn.innerHTML = btn.dataset.originalText;
    btn.disabled  = false;
  }
}

// ── NUMBER COUNTER ANIMATION ──────────────────────
function animateNumber(el, target, duration = 1000, prefix = '₹') {
  let start     = 0;
  const step    = target / (duration / 16);
  const timer   = setInterval(() => {
    start += step;
    if (start >= target) {
      el.textContent = prefix + Math.floor(target).toLocaleString('en-IN');
      clearInterval(timer);
    } else {
      el.textContent = prefix + Math.floor(start).toLocaleString('en-IN');
    }
  }, 16);
}

// Auto animate stat numbers on dashboard
document.querySelectorAll('.stat-info h3').forEach(el => {
  const text = el.textContent.trim();
  if (text.startsWith('₹') && !isNaN(text.replace('₹', '').replace(',', ''))) {
    const num = parseInt(text.replace('₹', '').replace(',', ''));
    animateNumber(el, num);
  }
});