/* William Li — personal site interactions
   - Mobile nav toggle
   - Smooth in-page scrolling with header offset
   - Scroll-spy active state for nav links
   - Dynamic footer year
*/

(() => {
  const header = document.querySelector('.site-header');
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.getElementById('nav-links');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function getHeaderHeight() {
    return header ? header.offsetHeight : 0;
  }

  function toggleNav(forceOpen = null) {
    const isOpen = navLinks.classList.contains('open');
    const next = forceOpen === null ? !isOpen : forceOpen;
    navLinks.classList.toggle('open', next);
    if (navToggle) {
      navToggle.setAttribute('aria-expanded', String(next));
    }
    // Prevent body scroll when menu is open on small screens
    document.body.style.overflow = next ? 'hidden' : '';
  }

  function initNavToggle() {
    if (!navToggle || !navLinks) return;
    navToggle.addEventListener('click', () => toggleNav());
    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navLinks.classList.contains('open')) toggleNav(false);
    });
    // Close when clicking a link
    navLinks.addEventListener('click', (e) => {
      const t = e.target;
      if (t && t.tagName === 'A') toggleNav(false);
    });
  }

  function smoothScrollTo(hash) {
    const id = hash.replace('#', '');
    const target = document.getElementById(id);
    if (!target) return;

    const offset = getHeaderHeight() + 8;
    const targetTop = target.getBoundingClientRect().top + window.pageYOffset - offset;

    window.scrollTo({
      top: Math.max(0, targetTop),
      behavior: prefersReduced ? 'auto' : 'smooth'
    });
  }

  function initSmoothAnchors() {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;
      const { hash } = link;
      if (!hash) return;
      const target = document.getElementById(hash.slice(1));
      if (!target) return;

      e.preventDefault();
      smoothScrollTo(hash);
      // Update hash without jumping
      history.pushState(null, '', hash);
    });

    // If page loads with a hash, adjust position
    window.addEventListener('load', () => {
      if (location.hash) {
        setTimeout(() => smoothScrollTo(location.hash), 0);
      }
    });
  }

  function initScrollSpy() {
    const sections = Array.from(document.querySelectorAll('main section[id]'));
    const links = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));

    if (!sections.length || !links.length) return;

    const linkForId = new Map();
    links.forEach((a) => {
      const id = a.getAttribute('href').slice(1);
      linkForId.set(id, a);
    });

    let activeId = null;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const id = entry.target.id;
          if (entry.isIntersecting) {
            activeId = id;
            links.forEach((a) => a.removeAttribute('aria-current'));
            const activeLink = linkForId.get(id);
            if (activeLink) activeLink.setAttribute('aria-current', 'true');
          }
        });
      },
      {
        // Trigger when section is near middle of viewport
        root: null,
        rootMargin: `-${Math.floor(window.innerHeight * 0.35)}px 0px -${Math.floor(window.innerHeight * 0.45)}px 0px`,
        threshold: 0
      }
    );

    sections.forEach((sec) => observer.observe(sec));
  }

  function setYear() {
    const y = document.getElementById('year');
    if (y) y.textContent = String(new Date().getFullYear());
  }

  // Initialize
  initNavToggle();
  initSmoothAnchors();
  initScrollSpy();
  setYear();
})();