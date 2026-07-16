(function () {
  window.Otokun = window.Otokun || {};

  let ctx = null;
  let lastPonAt = 0;
  const MIN_PON_INTERVAL_MS = 60;

  function getCtx() {
    if (!ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      ctx = new AudioCtx();
    }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  function playPon() {
    const now = performance.now();
    if (now - lastPonAt < MIN_PON_INTERVAL_MS) return;
    lastPonAt = now;
    const audioCtx = getCtx();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.13);
  }

  function playChime() {
    const audioCtx = getCtx();
    const notes = [523.25, 659.25, 783.99];
    notes.forEach((freq, i) => {
      const start = audioCtx.currentTime + i * 0.12;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, start);
      gain.gain.setValueAtTime(0.001, start);
      gain.gain.linearRampToValueAtTime(0.2, start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, start + 0.35);
      osc.connect(gain).connect(audioCtx.destination);
      osc.start(start);
      osc.stop(start + 0.4);
    });
  }

  window.Otokun.Audio = { playPon, playChime };
})();
