(function () {
  window.Otokun = window.Otokun || {};

  let voice = null;
  let queue = [];
  let speaking = false;

  function pickJapaneseVoice() {
    if (!window.speechSynthesis) return;
    const voices = speechSynthesis.getVoices();
    voice = voices.find((v) => v.lang === 'ja-JP') || voices.find((v) => (v.lang || '').startsWith('ja')) || null;
  }

  if (window.speechSynthesis) {
    speechSynthesis.onvoiceschanged = pickJapaneseVoice;
    pickJapaneseVoice();
  }

  function pump() {
    if (speaking || queue.length === 0) return;
    if (!window.speechSynthesis) {
      queue = [];
      return;
    }
    const next = queue.shift();
    const utter = new SpeechSynthesisUtterance(next.text);
    if (voice) utter.voice = voice;
    utter.lang = 'ja-JP';
    speaking = true;
    utter.onend = utter.onerror = () => {
      speaking = false;
      pump();
    };
    speechSynthesis.speak(utter);
  }

  function speak(text, opts) {
    const priority = (opts && opts.priority) || 'normal';
    if (priority === 'letter') {
      queue = queue.filter((item) => item.priority !== 'letter');
    }
    queue.push({ text, priority });
    pump();
  }

  window.Otokun.Speech = { speak };
})();
