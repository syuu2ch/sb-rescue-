(function () {
  window.Otokun = window.Otokun || {};

  const SEQ = ['e', 'n', 'd'];
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

      const k = (e.key || '').toLowerCase();
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
