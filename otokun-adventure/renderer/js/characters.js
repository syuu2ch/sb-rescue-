(function () {
  window.Otokun = window.Otokun || {};

  function svgWrap(inner, extraClass) {
    return `<svg viewBox="0 0 200 200" class="critter ${extraClass || ''}" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
  }

  function eyes(cx1, cx2, cy, r) {
    r = r || 3.5;
    return `<circle cx="${cx1}" cy="${cy}" r="${r}" fill="#2b2b2b"/><circle cx="${cx2}" cy="${cy}" r="${r}" fill="#2b2b2b"/>`;
  }

  function blush(cx1, cx2, cy) {
    return `<circle cx="${cx1}" cy="${cy}" r="5" fill="#FF9E9E" opacity="0.55"/><circle cx="${cx2}" cy="${cy}" r="5" fill="#FF9E9E" opacity="0.55"/>`;
  }

  // ---- おとくん (protagonist) ----
  function renderOtokun() {
    const inner = `
      <g class="otokun-body">
        <ellipse cx="100" cy="178" rx="26" ry="7" fill="#000" opacity="0.12"/>
        <g class="arm arm-left"><rect x="62" y="108" width="16" height="42" rx="8" fill="#FFDBB0"/></g>
        <g class="arm arm-right"><rect x="122" y="108" width="16" height="42" rx="8" fill="#FFDBB0"/></g>
        <rect x="78" y="100" width="44" height="46" rx="14" fill="#4A90D9"/>
        <rect x="80" y="140" width="17" height="30" rx="6" fill="#FFDBB0"/>
        <rect x="103" y="140" width="17" height="30" rx="6" fill="#FFDBB0"/>
        <rect x="78" y="135" width="44" height="18" rx="8" fill="#3B3B3B"/>
        <ellipse cx="88" cy="172" rx="10" ry="5" fill="#C0392B"/>
        <ellipse cx="112" cy="172" rx="10" ry="5" fill="#C0392B"/>
        <circle cx="100" cy="70" r="30" fill="#5B3A29"/>
        <circle cx="100" cy="76" r="25" fill="#FFDBB0"/>
        <path d="M 74 62 Q 100 48 126 62 L 126 70 Q 100 58 74 70 Z" fill="#5B3A29"/>
        ${eyes(90, 110, 78)}
        ${blush(82, 118, 88)}
        <path d="M 92 92 Q 100 97 108 92" stroke="#B5651D" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      </g>`;
    return svgWrap(inner, 'otokun');
  }

  // ---- パパ / ママ ----
  function renderPapa() {
    const inner = `
      <g>
        <ellipse cx="100" cy="182" rx="28" ry="7" fill="#000" opacity="0.12"/>
        <g class="arm arm-left"><rect x="58" y="100" width="16" height="48" rx="8" fill="#F3C89A"/></g>
        <g class="arm arm-right"><rect x="126" y="100" width="16" height="48" rx="8" fill="#F3C89A"/></g>
        <rect x="74" y="92" width="52" height="56" rx="12" fill="#4B6584"/>
        <rect x="80" y="146" width="18" height="34" rx="6" fill="#3B3B3B"/>
        <rect x="102" y="146" width="18" height="34" rx="6" fill="#3B3B3B"/>
        <circle cx="100" cy="62" r="28" fill="#F3C89A"/>
        <path d="M 74 52 Q 100 34 126 52 L 124 60 Q 100 44 76 60 Z" fill="#2F2F2F"/>
        <path d="M 90 76 Q 100 82 110 76" stroke="#2F2F2F" stroke-width="3" fill="none" stroke-linecap="round"/>
        ${eyes(88, 112, 60)}
      </g>`;
    return svgWrap(inner, 'papa');
  }

  function renderMama() {
    const inner = `
      <g>
        <ellipse cx="100" cy="184" rx="30" ry="7" fill="#000" opacity="0.12"/>
        <g class="arm arm-left"><rect x="60" y="100" width="15" height="44" rx="7.5" fill="#FBD8B5"/></g>
        <g class="arm arm-right"><rect x="125" y="100" width="15" height="44" rx="7.5" fill="#FBD8B5"/></g>
        <path d="M 68 96 Q 100 82 132 96 L 138 178 Q 100 192 62 178 Z" fill="#E4679E"/>
        <circle cx="100" cy="60" r="27" fill="#FBD8B5"/>
        <path d="M 70 56 Q 100 30 130 56 Q 132 90 122 100 Q 128 66 100 64 Q 72 66 78 100 Q 68 90 70 56 Z" fill="#3B2A22"/>
        ${eyes(88, 112, 58)}
        <path d="M 90 74 Q 100 79 110 74" stroke="#B5651D" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        ${blush(82, 118, 66)}
      </g>`;
    return svgWrap(inner, 'mama');
  }

  // ---- 動物たち ----
  const ANIMALS = {
    うさぎ: () => svgWrap(`
      <g class="ears">
        <ellipse cx="86" cy="45" rx="10" ry="34" fill="#FFFFFF" stroke="#DDD" stroke-width="1"/>
        <ellipse cx="114" cy="45" rx="10" ry="34" fill="#FFFFFF" stroke="#DDD" stroke-width="1"/>
        <ellipse cx="86" cy="48" rx="5" ry="24" fill="#FFC0CB"/>
        <ellipse cx="114" cy="48" rx="5" ry="24" fill="#FFC0CB"/>
      </g>
      <ellipse cx="100" cy="130" rx="42" ry="36" fill="#FFFFFF" stroke="#DDD" stroke-width="1"/>
      <circle cx="100" cy="86" r="30" fill="#FFFFFF" stroke="#DDD" stroke-width="1"/>
      ${eyes(90, 110, 88)}
      ${blush(80, 120, 96)}
      <ellipse cx="100" cy="98" rx="4" ry="3" fill="#FF9E9E"/>
    `, 'animal-usagi'),

    とり: () => svgWrap(`
      <g class="wing"><path d="M 118 100 Q 150 100 140 130 Q 120 128 112 112 Z" fill="#F2A65A"/></g>
      <ellipse cx="100" cy="120" rx="38" ry="34" fill="#FFC93C"/>
      <circle cx="100" cy="80" r="24" fill="#FFC93C"/>
      <path d="M 100 82 L 118 88 L 100 92 Z" fill="#F2711A"/>
      ${eyes(92, 108, 78, 3)}
      <path d="M 70 150 L 75 165 M 130 150 L 125 165" stroke="#F2711A" stroke-width="3" stroke-linecap="round"/>
    `, 'animal-tori'),

    いぬ: () => svgWrap(`
      <g class="ears">
        <ellipse cx="72" cy="72" rx="14" ry="22" fill="#8B5E3C"/>
        <ellipse cx="128" cy="72" rx="14" ry="22" fill="#8B5E3C"/>
      </g>
      <ellipse cx="100" cy="130" rx="42" ry="36" fill="#E8C39E"/>
      <circle cx="100" cy="82" r="30" fill="#F3D5B0"/>
      <ellipse cx="100" cy="94" rx="10" ry="7" fill="#F3D5B0"/>
      <circle cx="100" cy="96" r="4" fill="#3B3B3B"/>
      ${eyes(88, 112, 80)}
      <path d="M 150 130 Q 168 118 160 100" stroke="#8B5E3C" stroke-width="8" fill="none" stroke-linecap="round"/>
    `, 'animal-inu'),

    ねこ: () => svgWrap(`
      <g class="ears">
        <path d="M 72 60 L 62 30 L 92 52 Z" fill="#F2A65A"/>
        <path d="M 128 60 L 138 30 L 108 52 Z" fill="#F2A65A"/>
      </g>
      <ellipse cx="100" cy="130" rx="40" ry="34" fill="#F2A65A"/>
      <circle cx="100" cy="82" r="28" fill="#F7C68B"/>
      ${eyes(88, 112, 82)}
      <path d="M 60 88 L 82 90 M 60 96 L 82 94 M 140 88 L 118 90 M 140 96 L 118 94" stroke="#B5651D" stroke-width="1.5"/>
      <path d="M 145 150 Q 168 140 158 112" stroke="#F2A65A" stroke-width="8" fill="none" stroke-linecap="round"/>
    `, 'animal-neko'),

    くま: () => svgWrap(`
      <g class="ears">
        <circle cx="72" cy="52" r="16" fill="#8B5E3C"/>
        <circle cx="128" cy="52" r="16" fill="#8B5E3C"/>
      </g>
      <ellipse cx="100" cy="132" rx="46" ry="38" fill="#8B5E3C"/>
      <circle cx="100" cy="82" r="32" fill="#A9764F"/>
      <ellipse cx="100" cy="94" rx="14" ry="10" fill="#D9B48F"/>
      <circle cx="100" cy="96" r="4" fill="#3B3B3B"/>
      ${eyes(86, 114, 78)}
    `, 'animal-kuma'),

    きつね: () => svgWrap(`
      <g class="tail"><path d="M 150 140 Q 190 130 178 90 Q 165 100 155 130 Z" fill="#E8792A"/><path d="M 176 96 Q 182 108 172 122" stroke="#FFF" stroke-width="6" fill="none" stroke-linecap="round"/></g>
      <g class="ears">
        <path d="M 76 55 L 62 22 L 96 48 Z" fill="#E8792A"/>
        <path d="M 124 55 L 138 22 L 104 48 Z" fill="#E8792A"/>
      </g>
      <ellipse cx="100" cy="128" rx="40" ry="34" fill="#E8792A"/>
      <path d="M 70 128 Q 100 150 130 128 Q 120 140 100 142 Q 80 140 70 128 Z" fill="#FFF6EC"/>
      <circle cx="100" cy="82" r="28" fill="#EF8C3C"/>
      <path d="M 88 92 Q 100 106 112 92 Q 100 100 88 92 Z" fill="#FFF6EC"/>
      ${eyes(88, 112, 80)}
    `, 'animal-kitsune'),

    りす: () => svgWrap(`
      <g class="tail"><ellipse cx="150" cy="90" rx="26" ry="44" fill="#C77B3D" transform="rotate(18 150 90)"/></g>
      <ellipse cx="100" cy="132" rx="34" ry="32" fill="#C77B3D"/>
      <circle cx="100" cy="88" r="26" fill="#D68F52"/>
      ${eyes(90, 110, 86)}
      ${blush(82, 118, 94)}
      <ellipse cx="60" cy="130" rx="9" ry="7" fill="#8B5A2B"/>
    `, 'animal-risu'),

    かめ: () => svgWrap(`
      <ellipse cx="100" cy="128" rx="52" ry="40" fill="#3F9B5D"/>
      <path d="M 100 92 Q 130 96 140 128 Q 100 138 60 128 Q 70 96 100 92 Z" fill="#2E7D46"/>
      <circle cx="100" cy="86" r="34" fill="#2E7D46"/>
      <ellipse cx="100" cy="90" rx="20" ry="16" fill="#5BC27A"/>
      ${eyes(90, 110, 86)}
      <path d="M 78 100 L 122 100 M 100 78 L 100 100" stroke="#1F5C33" stroke-width="2" opacity="0.5"/>
    `, 'animal-kame'),

    たこ: () => svgWrap(`
      <g class="legs">
        <path d="M 70 140 Q 55 165 65 185" stroke="#D1477A" stroke-width="10" fill="none" stroke-linecap="round"/>
        <path d="M 88 150 Q 80 175 85 190" stroke="#D1477A" stroke-width="10" fill="none" stroke-linecap="round"/>
        <path d="M 112 150 Q 120 175 115 190" stroke="#D1477A" stroke-width="10" fill="none" stroke-linecap="round"/>
        <path d="M 130 140 Q 145 165 135 185" stroke="#D1477A" stroke-width="10" fill="none" stroke-linecap="round"/>
      </g>
      <ellipse cx="100" cy="100" rx="46" ry="42" fill="#E0568C"/>
      ${eyes(86, 114, 92, 6)}
      ${blush(78, 122, 104)}
    `, 'animal-tako'),

    ふくろう: () => svgWrap(`
      <g class="ears">
        <path d="M 78 50 L 68 24 L 92 44 Z" fill="#7A5C41"/>
        <path d="M 122 50 L 132 24 L 108 44 Z" fill="#7A5C41"/>
      </g>
      <g class="wing"><ellipse cx="66" cy="120" rx="16" ry="30" fill="#7A5C41"/><ellipse cx="134" cy="120" rx="16" ry="30" fill="#7A5C41"/></g>
      <ellipse cx="100" cy="128" rx="40" ry="42" fill="#9C7A54"/>
      <circle cx="100" cy="86" r="34" fill="#B3906A"/>
      <circle cx="86" cy="86" r="14" fill="#FFF"/>
      <circle cx="114" cy="86" r="14" fill="#FFF"/>
      ${eyes(86, 114, 86, 5)}
      <path d="M 96 98 L 100 106 L 104 98 Z" fill="#F2A65A"/>
    `, 'animal-fukurou'),
  };

  function renderAnimal(name) {
    const fn = ANIMALS[name];
    if (!fn) {
      return svgWrap(`<circle cx="100" cy="100" r="40" fill="#CCC"/>${eyes(90, 110, 95)}`, 'animal-unknown');
    }
    return fn();
  }

  window.Otokun = window.Otokun || {};
  window.Otokun.Characters = {
    renderOtokun,
    renderPapa,
    renderMama,
    renderAnimal,
    knownAnimals: () => Object.keys(ANIMALS),
  };
})();
