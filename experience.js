/* Lightweight, accessible enhancements. Works with the existing static site.
   No tracking, libraries, external requests, or content changes. */
(() => {
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.site-nav');
  const sections = [...document.querySelectorAll('main > section[id]')];
  const links = [...(nav?.querySelectorAll('a[href^="#"]') || [])];

  const progress = document.createElement('progress');
  progress.className = 'scroll-progress';
  progress.max = 100;
  progress.value = 0;
  progress.setAttribute('aria-label', 'Page reading progress');
  document.body.prepend(progress);

  const backToTop = document.createElement('a');
  backToTop.href = '#top';
  backToTop.className = 'back-to-top';
  backToTop.textContent = '↑';
  backToTop.setAttribute('aria-label', 'Back to top');
  document.body.append(backToTop);

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

  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  if (!reducedMotion && 'IntersectionObserver' in window) {
    const nodes = document.querySelectorAll(
      '.hero-copy > .hero-eyebrow, .hero-copy > h1, .hero-copy > .role, .hero-copy > .hero-intro, ' +
      '.hero-actions, .hero-expertise, .hero-photo, .section-heading, ' +
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
    nodes.forEach((node, index) => {
      node.classList.add('reveal');
      node.style.setProperty('--reveal-delay', String(Math.min(index % 4, 3) * 70) + 'ms');
      observer.observe(node);
    });
    document.documentElement.classList.add('motion-ready');
  }
})();
