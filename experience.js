/* Lightweight, accessible enhancements. Works with the existing static site.
   No tracking, libraries, external requests, or content changes. */
(() => {
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.site-nav');
  const sections = [...document.querySelectorAll('main > section[id]')];
  const links = [...(nav?.querySelectorAll('a[href^="#"]') || [])];
  const researchSection = document.getElementById('research');
  const researchLinks = [...document.querySelectorAll('.research-subnav a[href^="#"]')];
  const researchTargets = researchLinks.map((link) => ({
    link,
    target: document.getElementById(link.getAttribute('href').slice(1))
  }));
  // Pair existing abstract toggles with their panels for screen readers.
  document.querySelectorAll('.abstract-toggle').forEach((button, i) => {
    const panel = button.closest('article')?.querySelector('.abstract-panel');
    if (!panel) return;
    if (!panel.id) panel.id = 'paper-abstract-' + (i + 1);
    button.setAttribute('aria-controls', panel.id);
  });

  const progress = document.createElement('progress');
  progress.className = 'scroll-progress';
  progress.max = 100;
  progress.value = 0;
  progress.setAttribute('aria-label', 'Page reading progress');
  document.body.prepend(progress);

  // Use an explicit scroll action: hash navigation to a sticky header is
  // inconsistent in some browsers and may appear to do nothing.
  const goToTop = () => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    try {
      window.scrollTo({ top: 0, left: 0, behavior: reduce ? 'auto' : 'smooth' });
    } catch {
      window.scrollTo(0, 0);
    }
  };

  const backToTop = document.createElement('button');
  backToTop.type = 'button';
  backToTop.className = 'back-to-top';
  backToTop.textContent = '↑';
  backToTop.setAttribute('aria-label', 'Back to top');
  backToTop.addEventListener('click', goToTop);
  document.body.append(backToTop);

  document.querySelectorAll('a[href="#top"]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      goToTop();
    });
  });

  let scheduled = false;
  function refreshScrollUI() {
    scheduled = false;
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    progress.value = scrollable > 0 ? Math.min(100, Math.max(0, Math.round(window.scrollY / scrollable * 100))) : 0;
    header?.classList.toggle('is-scrolled', window.scrollY > 24);
    backToTop.classList.toggle('is-visible', window.scrollY > 540);

    let current = '';
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= Math.max(150, window.innerHeight * .28)) {
        current = section.id;
      }
    }
    for (const link of links) {
      const active = current && link.getAttribute('href') === '#' + current;
      link.classList.toggle('is-active', Boolean(active));
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
    // Indicate the subsection currently being read without hiding any papers.
    const region = researchSection?.getBoundingClientRect();
    const readingResearch = Boolean(region && region.top <= 180 && region.bottom >= 180);
    let activeResearch = '';
    if (readingResearch) {
      for (const { target } of researchTargets) {
        if (target && target.getBoundingClientRect().top <= 190) activeResearch = target.id;
      }
    }
    for (const { link, target } of researchTargets) {
      const isActive = Boolean(target && activeResearch === target.id);
      link.classList.toggle('is-active', isActive);
      if (isActive) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  }
  const onScroll = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(refreshScrollUI);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  window.addEventListener('load', refreshScrollUI);
  refreshScrollUI();

  // Make the existing responsive menu easier to use with keyboard or touch.
  const menuButton = document.querySelector('.menu-button');
  const closeMenu = () => {
    if (!nav?.classList.contains('open')) return;
    nav.classList.remove('open');
    menuButton?.setAttribute('aria-expanded','false');
  };
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav?.classList.contains('open')) {
      closeMenu();
      menuButton?.focus();
    }
  });
  document.addEventListener('pointerdown', (event) => {
    if (nav?.classList.contains('open') && !header?.contains(event.target)) closeMenu();
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 980) closeMenu();
  }, { passive:true });

  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  if (!reducedMotion && 'IntersectionObserver' in window) {
    const nodes = document.querySelectorAll(
      '.hero-copy > .hero-eyebrow, .hero-copy > h1, .hero-copy > .role, .hero-copy > .hero-intro, ' +
      '.hero-actions, .hero-expertise, .hero-photo, .section-heading, .subsection-heading, ' +
      '.education-row, .experience-card, .feature-paper, .paper-item, .project-card, ' +
      '.timeline-item, .recognition-grid > article, .activity-row, .reference-grid > article, ' +
      '.contact-card, .service-column, .grant-grid > article'
    );
    const observer = new IntersectionObserver((entries, obs) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      }
    }, { threshold: .045, rootMargin: '0px 0px -5% 0px' });
    nodes.forEach((node) => {
      node.classList.add('reveal');
      observer.observe(node);
    });
    document.documentElement.classList.add('motion-ready');
  }
})();
