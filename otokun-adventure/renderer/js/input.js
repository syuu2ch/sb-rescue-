(function () {
  window.Otokun = window.Otokun || {};

  function optionHeld() {
    return window.Otokun.SecretExit && window.Otokun.SecretExit.isOptionHeld();
  }

  window.addEventListener('keydown', (e) => {
    if (optionHeld()) return;
    window.Otokun.Director.handleAdvance();
  });

  window.addEventListener('pointerdown', (e) => {
    if (optionHeld()) return;
    window.Otokun.Director.handleAdvance();
  });
})();
