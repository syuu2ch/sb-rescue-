(function () {
  window.Otokun = window.Otokun || {};
  const Characters = () => window.Otokun.Characters;

  const el = {
    stage: () => document.getElementById('stage'),
    titleScreen: () => document.getElementById('title-screen'),
    gameScreen: () => document.getElementById('game-screen'),
    meterBar: () => document.getElementById('meter-bar'),
    wordSlots: () => document.getElementById('word-slots'),
    familyLayer: () => document.getElementById('family-layer'),
    companionTrain: () => document.getElementById('companion-train'),
    otokunLayer: () => document.getElementById('otokun-layer'),
    spotlight: () => document.getElementById('spotlight'),
    spotlightAnimal: () => document.getElementById('spotlight-animal'),
    spotlightWord: () => document.getElementById('spotlight-word'),
    factPanel: () => document.getElementById('fact-panel'),
    transitionOverlay: () => document.getElementById('transition-overlay'),
  };

  let familyIdleTimer = null;

  function dismissTitle() {
    el.titleScreen().classList.add('hidden');
    el.gameScreen().classList.remove('hidden');
    el.otokunLayer().innerHTML = Characters().renderOtokun();
  }

  function setStageBackground(stageDef) {
    const stageEl = el.stage();
    stageEl.className = 'stage ' + stageDef.bgClass;
  }

  function showEmptySlots(word) {
    const wrap = el.wordSlots();
    wrap.innerHTML = '';
    for (let i = 0; i < word.length; i++) {
      const slot = document.createElement('div');
      slot.className = 'letter-slot';
      slot.textContent = '';
      wrap.appendChild(slot);
    }
  }

  function revealLetter(word, revealedCount) {
    const wrap = el.wordSlots();
    const slot = wrap.children[revealedCount - 1];
    if (!slot) return;
    slot.textContent = word[revealedCount - 1];
    slot.classList.add('pop');
  }

  function updateMeter(fraction) {
    const bar = el.meterBar();
    bar.style.width = `${Math.min(1, Math.max(0, fraction)) * 100}%`;
  }

  function bounceOtokun() {
    const layer = el.otokunLayer();
    layer.classList.remove('pose-bounce');
    void layer.offsetWidth;
    layer.classList.add('pose-bounce');
  }

  function celebrateWordComplete(animalName, word, onDone) {
    const layer = el.otokunLayer();
    layer.classList.add('pose-run');

    const spot = el.spotlight();
    el.spotlightAnimal().innerHTML = Characters().renderAnimal(animalName);
    el.spotlightWord().textContent = word;
    spot.classList.remove('hidden');
    spot.classList.add('show');

    window.Otokun.Audio.playChime();

    setTimeout(() => {
      layer.classList.remove('pose-run');
      spot.classList.remove('show');
      spot.classList.add('hidden');
      if (onDone) onDone();
    }, 1400);
  }

  function addCompanion(animalName) {
    const train = el.companionTrain();
    const holder = document.createElement('div');
    holder.className = `companion companion-${animalName}`;
    holder.dataset.animal = animalName;
    holder.innerHTML = Characters().renderAnimal(animalName);
    train.appendChild(holder);
    void holder.offsetWidth;
    holder.classList.add('pop-in');
  }

  function renderCompanionTrain(companions) {
    const train = el.companionTrain();
    train.innerHTML = '';
    companions.forEach((c) => {
      const holder = document.createElement('div');
      holder.className = `companion companion-${c.name}`;
      holder.dataset.animal = c.name;
      holder.innerHTML = Characters().renderAnimal(c.name);
      train.appendChild(holder);
    });
  }

  function showFamily(names) {
    const layer = el.familyLayer();
    layer.innerHTML = '';
    const builders = { 'パパ': Characters().renderPapa, 'ママ': Characters().renderMama };
    names.forEach((name) => {
      const holder = document.createElement('div');
      holder.className = `family-member family-${name}`;
      holder.innerHTML = (builders[name] || Characters().renderPapa)();
      layer.appendChild(holder);
    });
    layer.classList.add('show');

    clearInterval(familyIdleTimer);
    familyIdleTimer = setInterval(() => {
      const members = layer.querySelectorAll('.family-member');
      if (members.length === 0) return;
      const target = members[Math.floor(Math.random() * members.length)];
      target.classList.remove('wave');
      void target.offsetWidth;
      target.classList.add('wave');
    }, 3500);
  }

  function hideFamily() {
    clearInterval(familyIdleTimer);
    familyIdleTimer = null;
    el.familyLayer().classList.remove('show');
    el.familyLayer().innerHTML = '';
  }

  function nudgeFamily() {
    const layer = el.familyLayer();
    const members = layer.querySelectorAll('.family-member');
    if (members.length === 0) return;
    const target = members[Math.floor(Math.random() * members.length)];
    target.classList.remove('wave');
    void target.offsetWidth;
    target.classList.add('wave');
  }

  function playHappeningAnimation() {
    const train = el.companionTrain();
    const candidates = train.querySelectorAll('.companion');
    const layer = el.otokunLayer();
    const pool = [layer, ...candidates];
    const target = pool[Math.floor(Math.random() * pool.length)];
    if (!target) return;
    target.classList.remove('happening');
    void target.offsetWidth;
    target.classList.add('happening');
  }

  function startFactPanel(animals) {
    const panel = el.factPanel();
    panel.innerHTML = '';
    panel.classList.remove('hidden');
    panel.classList.add('show');
    animals.forEach((a, i) => {
      const card = document.createElement('div');
      card.className = `fact-slot fact-slot-${i} dim`;
      card.dataset.animal = a.name;
      card.innerHTML = `<div class="fact-critter">${Characters().renderAnimal(a.name)}</div><div class="fact-text"></div>`;
      panel.appendChild(card);
    });
  }

  function highlightFact(index, animalName, factText) {
    const panel = el.factPanel();
    const card = panel.querySelector(`.fact-slot-${index}`);
    if (!card) return;
    card.classList.remove('dim');
    card.classList.add('active', 'trait-wiggle');
    card.querySelector('.fact-text').textContent = factText;
  }

  function endFactPanel() {
    const panel = el.factPanel();
    panel.classList.remove('show');
    panel.classList.add('hidden');
    panel.innerHTML = '';
  }

  function playTransitionCelebration(onDone) {
    const overlay = el.transitionOverlay();
    overlay.classList.remove('hidden');
    overlay.classList.add('show');
    setTimeout(() => {
      overlay.classList.remove('show');
      overlay.classList.add('hidden');
      if (onDone) onDone();
    }, 1800);
  }

  window.Otokun.UI = {
    dismissTitle,
    setStageBackground,
    showEmptySlots,
    revealLetter,
    updateMeter,
    bounceOtokun,
    celebrateWordComplete,
    addCompanion,
    renderCompanionTrain,
    showFamily,
    hideFamily,
    nudgeFamily,
    playHappeningAnimation,
    startFactPanel,
    highlightFact,
    endFactPanel,
    playTransitionCelebration,
  };
})();
