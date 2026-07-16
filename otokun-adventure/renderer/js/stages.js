(function () {
  window.Otokun = window.Otokun || {};

  const STAGE_ROTATION = [
    { key: 'meadow', label: '草原', bgClass: 'stage-meadow', words: ['うさぎ', 'とり', 'いぬ', 'ねこ'] },
    { key: 'forest', label: '森', bgClass: 'stage-forest', words: ['くま', 'きつね', 'りす'] },
    { key: 'beach', label: '海辺', bgClass: 'stage-beach', words: ['かめ', 'たこ'] },
    { key: 'snow', label: '雪山', bgClass: 'stage-snow', words: ['きつね', 'うさぎ', 'くま'] },
    { key: 'night', label: '夜空', bgClass: 'stage-night', words: ['ふくろう', 'ねこ', 'うさぎ'] },
    { key: 'home', label: 'おうち', bgClass: 'stage-home', words: ['いぬ', 'ねこ'], hasFamily: true },
  ];

  window.Otokun.Stages = {
    ROTATION: STAGE_ROTATION,
    nextIndex: (i) => (i + 1) % STAGE_ROTATION.length,
  };
})();
