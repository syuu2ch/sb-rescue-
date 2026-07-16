(function () {
  window.Otokun = window.Otokun || {};

  // Matched against e.code (physical key position), not e.key: on macOS,
  // holding Option turns E/N/U/I into dead-key accent modifiers, so e.key
  // stops being a plain letter while Option is held. e.code is layout- and
  // modifier-independent, so it still reports 'KeyE'/'KeyN'/'KeyD' correctly.
  const SEQ = ['KeyE', 'KeyN', 'KeyD'];
  let optionHeld = false;
  let seqIndex = 0;
  let armed = false;

  function isOptionKey(e) {
    return e.key === 'Alt';
  }

  window.addEventListener(
    'keydown',
    (e) => {
      if (isOptionKey(e)) {
        optionHeld = true;
        seqIndex = 0;
        armed = false;
        return;
      }
      if (!optionHeld) return;

      const k = e.code;
      if (k === SEQ[seqIndex]) {
        seqIndex += 1;
        if (seqIndex === SEQ.length) armed = true;
        e.stopImmediatePropagation();
        e.preventDefault();
      } else {
        seqIndex = 0;
        armed = false;
      }
    },
    true
  );

  window.addEventListener(
    'keyup',
    (e) => {
      if (isOptionKey(e)) {
        if (armed && window.otokunAPI) {
          window.otokunAPI.secretQuit();
        }
        optionHeld = false;
        seqIndex = 0;
        armed = false;
      }
    },
    true
  );

  window.Otokun.SecretExit = {
    isOptionHeld: () => optionHeld,
  };
})();
