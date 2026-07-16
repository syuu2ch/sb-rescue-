(function () {
  window.Otokun = window.Otokun || {};

  function boot() {
    window.Otokun.Speech.speak(window.Otokun.Content.TITLE_TEXT, { priority: 'word' });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
