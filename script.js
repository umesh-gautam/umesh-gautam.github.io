const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('.site-nav');

if (menuButton && nav) {
  menuButton.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      nav.classList.remove('open');
      menuButton.setAttribute('aria-expanded', 'false');
    });
  });
}

document.querySelectorAll('.abstract-toggle').forEach((button) => {
  const closedLabel = button.textContent.trim();
  button.dataset.closedLabel = closedLabel;

  button.addEventListener('click', () => {
    const panel = button.closest('article')?.querySelector('.abstract-panel');
    if (!panel) return;

    const nowOpen = panel.hasAttribute('hidden');
    panel.toggleAttribute('hidden');
    button.setAttribute('aria-expanded', String(nowOpen));
    button.textContent = nowOpen ? 'Hide abstract' : button.dataset.closedLabel;
  });
});

const year = document.getElementById('year');
if (year) year.textContent = String(new Date().getFullYear());
