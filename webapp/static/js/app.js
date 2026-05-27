// Подтверждение перед опасными действиями + автоматическое скрытие success-блоков
document.addEventListener('htmx:afterSwap', (e) => {
  // подсветить новые блоки
  e.detail.target.classList.add('animate-pulse');
  setTimeout(() => e.detail.target.classList.remove('animate-pulse'), 600);
});
