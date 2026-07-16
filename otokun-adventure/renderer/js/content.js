(function () {
  window.Otokun = window.Otokun || {};

  const TITLE_TEXT = 'おとくんの　ぼうけん！！';

  const PRAISE_LINES = [
    'やったね！',
    'すごいね！',
    'じょうずだね！',
    'わーい！',
    'たのしいね！',
  ];

  const HAPPENING_LINES = [
    'あはは！',
    'おっとっと！',
    'へへっ！',
  ];

  const FACTS = {
    うさぎ: 'うさぎさんは　みみが　ながいよ',
    とり: 'とりさんは　そらを　とぶんだよ',
    いぬ: 'いぬさんは　わんわんって　なくよ',
    ねこ: 'ねこさんは　にゃーって　なくよ',
    くま: 'くまさんは　はちみつが　だいすきだよ',
    きつね: 'きつねさんは　しっぽが　ふさふさだよ',
    りす: 'りすさんは　どんぐりを　あつめるよ',
    かめ: 'かめさんは　こうらを　しょってるよ',
    たこ: 'たこさんは　あしが　やっつも　あるよ',
    ふくろう: 'ふくろうさんは　よるに　めが　さめるよ',
  };

  function pickRandom(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  window.Otokun.Content = {
    TITLE_TEXT,
    pickPraiseLine: () => pickRandom(PRAISE_LINES),
    pickHappeningLine: () => pickRandom(HAPPENING_LINES),
    factFor: (animalName) => FACTS[animalName] || `${animalName}さんだよ`,
  };
})();
