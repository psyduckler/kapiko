/* ============================================
   kapiko.ai — JavaScript
   Particles · Scroll animations · Nav
   ============================================ */

'use strict';

// === Navigation scroll state ===
(function initNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;

  function updateNav() {
    if (window.scrollY > 60) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', updateNav, { passive: true });
  updateNav();
})();


// === Scroll-triggered fade-ins ===
(function initFadeIn() {
  const elements = document.querySelectorAll('.fade-in');
  if (!elements.length) return;

  // Use IntersectionObserver if available
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Stagger children within the same parent group
            const siblings = entry.target.parentElement
              ? entry.target.parentElement.querySelectorAll('.fade-in:not(.visible)')
              : [];

            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    elements.forEach((el, i) => {
      // Stagger delay based on position in the DOM
      el.style.transitionDelay = `${(i % 4) * 0.08}s`;
      observer.observe(el);
    });
  } else {
    // Fallback: show all
    elements.forEach((el) => el.classList.add('visible'));
  }
})();


// === Particle Canvas ===
(function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let W, H, particles, animId;

  const CONFIG = {
    count: 55,
    minRadius: 0.5,
    maxRadius: 2.2,
    minSpeed: 0.06,
    maxSpeed: 0.22,
    colors: [
      'rgba(240,160,48,',   // amber
      'rgba(247,192,96,',   // amber-light
      'rgba(26,85,104,',    // teal
      'rgba(180,220,255,',  // cool highlight
    ],
    connectionDist: 130,
    maxConnections: 4,
  };

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function randomBetween(a, b) {
    return a + Math.random() * (b - a);
  }

  function createParticle() {
    const color = CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)];
    const alpha = randomBetween(0.2, 0.7);
    return {
      x: randomBetween(0, W),
      y: randomBetween(0, H),
      r: randomBetween(CONFIG.minRadius, CONFIG.maxRadius),
      vx: randomBetween(-1, 1) * randomBetween(CONFIG.minSpeed, CONFIG.maxSpeed),
      vy: randomBetween(-1, 1) * randomBetween(CONFIG.minSpeed, CONFIG.maxSpeed),
      color,
      alpha,
      baseAlpha: alpha,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: randomBetween(0.005, 0.02),
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: CONFIG.count }, createParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Update + draw particles
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // Move
      p.x += p.vx;
      p.y += p.vy;

      // Wrap edges
      if (p.x < -10) p.x = W + 10;
      else if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      else if (p.y > H + 10) p.y = -10;

      // Pulse alpha gently
      p.pulse += p.pulseSpeed;
      p.alpha = p.baseAlpha * (0.7 + 0.3 * Math.sin(p.pulse));

      // Draw particle
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + p.alpha + ')';
      ctx.fill();

      // Draw connections
      let connCount = 0;
      for (let j = i + 1; j < particles.length && connCount < CONFIG.maxConnections; j++) {
        const q = particles[j];
        const dx = p.x - q.x;
        const dy = p.y - q.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < CONFIG.connectionDist) {
          const lineAlpha = (1 - dist / CONFIG.connectionDist) * 0.12;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(240,160,48,${lineAlpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
          connCount++;
        }
      }
    }

    animId = requestAnimationFrame(draw);
  }

  // Reduce particles & animation on low-power preference
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) {
    // Just show a few static dots, no animation
    CONFIG.count = 12;
    init();
    draw();
    setTimeout(() => cancelAnimationFrame(animId), 100);
    return;
  }

  init();
  draw();

  // Resize handler
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      cancelAnimationFrame(animId);
      init();
      draw();
    }, 200);
  }, { passive: true });
})();


// === Smooth scroll for anchor links ===
(function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      const id = link.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (!target) return;

      e.preventDefault();
      const navH = document.getElementById('nav')?.offsetHeight || 64;
      const top = target.getBoundingClientRect().top + window.scrollY - navH;

      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();


// === Newsletter form handler ===
function handleSubscribe(e) {
  e.preventDefault();
  const form = e.target;
  const input = form.querySelector('input[type="email"]');
  const btn = form.querySelector('button');

  if (!input || !btn) return;

  const originalText = btn.textContent;
  btn.textContent = 'subscribed ✓';
  btn.disabled = true;
  input.disabled = true;
  btn.style.background = 'var(--teal-light)';

  // Reset after 4s
  setTimeout(() => {
    btn.textContent = originalText;
    btn.disabled = false;
    input.disabled = false;
    input.value = '';
    btn.style.background = '';
  }, 4000);
}


// === Active nav link highlighting ===
(function initActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');

  if (!sections.length || !navLinks.length) return;

  function onScroll() {
    const scrollY = window.scrollY;
    let current = '';

    sections.forEach((section) => {
      const top = section.offsetTop - 120;
      const bottom = top + section.offsetHeight;
      if (scrollY >= top && scrollY < bottom) {
        current = section.id;
      }
    });

    navLinks.forEach((link) => {
      const href = link.getAttribute('href').slice(1);
      link.style.color = href === current ? 'var(--amber-light)' : '';
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();


// === Parallax subtle effect on hero ===
(function initHeroParallax() {
  const heroContent = document.querySelector('.hero-content');
  if (!heroContent) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) return;

  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y < window.innerHeight) {
      heroContent.style.transform = `translateY(${y * 0.18}px)`;
      heroContent.style.opacity = 1 - y / (window.innerHeight * 0.9);
    }
  }, { passive: true });
})();
