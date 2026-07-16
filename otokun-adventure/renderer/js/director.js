(function () {
  window.Otokun = window.Otokun || {};

  const METER_MAX = 12;
  const METER_INCREMENT = 1;
  const STEPS_PER_CHEST = 3;
  const PRAISE_CHANCE = 0.35;
  const HAPPENING_CHANCE = 0.05;
  const FAMILY_NUDGE_CHANCE = 0.08;
  const FACT_DURATION_MS = 3200;

  let stageIndex = 0;
  let currentWord = null;
  let revealedCount = 0;
  let companions = [];
  let meterValue = 0;
  let totalCollected = 0;
  let phase = 'title';
  let usedWordsThisStage = [];
  let stepsSinceChest = 0;

  function Stages() { return window.Otokun.Stages; }
  function UI() { return window.Otokun.UI; }
  function Speech() { return window.Otokun.Speech; }
  function Audio() { return window.Otokun.Audio; }
  function Content() { return window.Otokun.Content; }

  function currentStageDef() {
    return Stages().ROTATION[stageIndex];
  }

  function chooseWord() {
    const pool = currentStageDef().words;
    let candidates = pool.filter((w) => !usedWordsThisStage.includes(w));
    if (candidates.length === 0) {
      usedWordsThisStage = [];
      candidates = pool;
    }
    const word = candidates[Math.floor(Math.random() * candidates.length)];
    usedWordsThisStage.push(word);
    return word;
  }

  function pickNewWord() {
    currentWord = chooseWord();
    revealedCount = 0;
    UI().showEmptySlots(currentWord);
  }

  function enterStage() {
    const def = currentStageDef();
    UI().setStageBackground(def);
    UI().hideFamily();
    if (def.hasFamily) UI().showFamily(['パパ', 'ママ']);
  }

  function start() {
    phase = 'playing';
    UI().dismissTitle();
    enterStage();
    pickNewWord();
  }

  function handleAdvance() {
    if (phase === 'title') {
      start();
      return;
    }
    if (phase !== 'playing') return;

    // Every press: おとくん takes a visible step forward, always and
    // unconditionally, so mashing always feels responsive.
    stepsSinceChest += 1;
    UI().bounceOtokun();
    Audio().playPon();

    meterValue += METER_INCREMENT;
    UI().updateMeter(meterValue / METER_MAX);

    if (Math.random() < HAPPENING_CHANCE) {
      UI().playHappeningAnimation();
      Speech().speak(Content().pickHappeningLine(), { priority: 'happening' });
    }
    if (currentStageDef().hasFamily && Math.random() < FAMILY_NUDGE_CHANCE) {
      UI().nudgeFamily();
    }

    // Every few steps: a treasure chest appears and reveals the next
    // letter of the word おとくん is spelling out.
    if (stepsSinceChest >= STEPS_PER_CHEST) {
      stepsSinceChest = 0;
      phase = 'chestOpening';
      UI().openTreasureChest(() => {
        revealedCount += 1;
        UI().revealLetter(currentWord, revealedCount);
        Speech().speak(currentWord[revealedCount - 1], { priority: 'letter' });
        if (Math.random() < PRAISE_CHANCE) {
          Speech().speak(Content().pickPraiseLine(), { priority: 'praise' });
        }

        if (revealedCount === currentWord.length) {
          onWordComplete();
        } else {
          phase = 'playing';
          if (meterValue >= METER_MAX) onStageMeterFull();
        }
      });
    } else if (meterValue >= METER_MAX) {
      onStageMeterFull();
    }
  }

  function onWordComplete() {
    const animalName = currentWord;
    phase = 'celebrating';
    UI().celebrateWordComplete(animalName, currentWord, () => {
      companions.push({ name: animalName });
      UI().addCompanion(animalName);
      totalCollected += 1;

      if (totalCollected % 3 === 0) {
        phase = 'characteristicsTime';
        runCharacteristicsSequence(companions.slice(-3));
      } else if (meterValue >= METER_MAX) {
        onStageMeterFull();
      } else {
        phase = 'playing';
        pickNewWord();
      }
    });
  }

  function runCharacteristicsSequence(animals) {
    UI().startFactPanel(animals);
    animals.forEach((a, i) => {
      setTimeout(() => {
        const fact = Content().factFor(a.name);
        UI().highlightFact(i, a.name, fact);
        Speech().speak(fact, { priority: 'fact' });
      }, i * FACT_DURATION_MS);
    });
    setTimeout(() => {
      UI().endFactPanel();
      if (meterValue >= METER_MAX) {
        onStageMeterFull();
      } else {
        phase = 'playing';
        pickNewWord();
      }
    }, animals.length * FACT_DURATION_MS);
  }

  function onStageMeterFull() {
    phase = 'stageTransition';
    UI().playTransitionCelebration(() => {
      stageIndex = Stages().nextIndex(stageIndex);
      meterValue = 0;
      usedWordsThisStage = [];
      UI().updateMeter(0);
      enterStage();
      UI().renderCompanionTrain(companions);
      phase = 'playing';
      pickNewWord();
    });
  }

  window.Otokun.Director = { handleAdvance };
})();
