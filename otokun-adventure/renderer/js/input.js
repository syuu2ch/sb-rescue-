(function () {
  window.Otokun = window.Otokun || {};

  window.addEventListener('keydown', () => {
    window.Otokun.Director.handleAdvance();
  });

  window.addEventListener('pointerdown', () => {
    window.Otokun.Director.handleAdvance();
  });
})();
