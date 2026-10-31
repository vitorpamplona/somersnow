/* Street-corner illustration for the "Who clears this?" map, drawn in the same style as the
   "Down to the pavement" scene (shovel.js): the morning after a storm, path shoveled, banks on each side.
   With hot=true it adds tappable hotspots, one per part of the street (keys match ui.who in i18n/en.js). */
import { lumpy } from './shovel.js';

export function corner(id, hot) {
  const SW = '#5E6C7B'; const BARE = '#6E7C8C'; const SNOW = '#FFFFFF'; const SHADE = '#B9CBDD'; const SOFT = '#E7EEF5';
  const bank = (x, y, w, h, seed, amp = 5, step = 26) => {
    const d = lumpy(x, y, w, h, seed, amp, step);
    return `<path d="${d}" fill="${SHADE}" transform="translate(0 4)"/><path d="${d}" fill="${SNOW}"/>`;
  };
  const windows = [];
  for (let row = 0; row < 2; row++) for (let c = 0; c < 6; c++) {
    if (row === 1 && (c === 2 || c === 3)) continue;
    windows.push(`<rect x="${34 + c * 78}" y="${26 + row * 70}" width="40" height="42" rx="3"/>`);
  }
  const joints = Array.from({ length: 9 }, (_, i) => `<path d="M${64 * (i + 1)} 256 V316" stroke="#5B6979" stroke-width="2"/>`).join('')
    + Array.from({ length: 4 }, (_, i) => `<path d="M535 ${64 * (i + 1) - 8} H595" stroke="#5B6979" stroke-width="2"/>`).join('');

  return `<svg id="${id}" class="scene" viewBox="0 0 800 560" role="img" aria-label="Top view of a Somerville street corner after a storm: a building with front stairs, the shoveled sidewalks along two streets, a curb ramp, a crosswalk, a bus stop, a hydrant and a storm drain">
  <defs><clipPath id="${id}-clip"><rect width="800" height="560"/></clipPath></defs>
  <g clip-path="url(#${id}-clip)">
  <rect width="800" height="560" fill="#10243A"/>
  <!-- building, front door and stairs -->
  <rect x="0" y="0" width="516" height="226" fill="#2B5482"/>
  <g fill="#F4C95D" opacity=".9">${windows.join('')}</g>
  <rect x="230" y="140" width="56" height="52" rx="3" fill="#10243A"/>
  <rect x="210" y="192" width="96" height="12" fill="#C9D3DD"/><rect x="204" y="204" width="108" height="11" fill="#B5C1CD"/><rect x="198" y="215" width="120" height="11" fill="#9AA8B6"/>
  <rect x="454" y="150" width="10" height="74" fill="#A9C4E4"/><rect x="448" y="218" width="22" height="8" rx="2" fill="#A9C4E4"/>
  <!-- sidewalks, curb, streets -->
  <rect x="0" y="226" width="612" height="114" fill="${SW}"/>
  <rect x="516" y="0" width="96" height="340" fill="${SW}"/>
  <rect x="0" y="340" width="624" height="12" fill="#9AA8B6"/>
  <rect x="612" y="0" width="12" height="352" fill="#9AA8B6"/>
  <g fill="#fff">${Array.from({ length: 8 }, (_, i) => `<rect x="535" y="${362 + i * 25}" width="60" height="13"/>`).join('')}</g>
  <path d="M0 474 H505 M640 474 H800" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <path d="M712 0 V336" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <!-- the shoveled path and its banks -->
  <rect x="0" y="256" width="595" height="60" fill="${BARE}"/>
  <rect x="535" y="0" width="60" height="256" fill="${BARE}"/>
  ${joints}
  ${bank(-10, 226, 194, 30, 3)}${bank(320, 226, 196, 30, 5)}
  ${bank(516, -10, 19, 266, 7, 4, 22)}${bank(595, -10, 22, 326, 9, 4, 22)}
  ${bank(-10, 316, 100, 26, 11)}${bank(180, 316, 196, 26, 13)}${bank(446, 316, 89, 26, 15)}
  <ellipse cx="430" cy="240" rx="40" ry="6" fill="${SOFT}"/><ellipse cx="80" cy="330" rx="30" ry="5" fill="${SOFT}"/>
  <!-- curb ramp with its yellow warning strip -->
  <path d="M519 316 H535 V352 Z M611 316 H595 V352 Z" fill="#7D8A98"/>
  <rect x="535" y="316" width="60" height="26" fill="#8C99A7"/>
  <rect x="535" y="338" width="60" height="14" fill="#F4C95D"/>
  <g fill="#C79A1F">${Array.from({ length: 10 }, (_, i) => `<circle cx="${541 + (i % 5) * 12}" cy="${342 + Math.floor(i / 5) * 6}" r="1.8"/>`).join('')}</g>
  <!-- bus stop: sign at the curb, a gap cut through the bank to the bus door -->
  <rect x="102" y="318" width="52" height="26" rx="5" fill="#FF8A3D" stroke="#10243A" stroke-width="3"/>
  <text x="128" y="337" text-anchor="middle" class="cap" font-size="16" fill="#10243A">BUS</text>
  <!-- hydrant, dug out all around -->
  <circle cx="412" cy="330" r="22" fill="${BARE}"/>
  <circle cx="412" cy="330" r="10" fill="#D9412B"/><rect x="398" y="326" width="28" height="8" rx="3" fill="#D9412B"/><circle cx="412" cy="330" r="4" fill="#8F2414"/>
  <!-- storm drain in the gutter, kept open -->
  <rect x="442" y="354" width="46" height="14" rx="2" fill="#2E3D4F"/><path d="M450 356v10M458 356v10M466 356v10M474 356v10M482 356v10" stroke="#8C9BAB" stroke-width="2"/>
  </g>
  ${hot ? `
  <g>
    <rect class="hot" data-k="building" tabindex="0" role="button" aria-label="Stairs and exits" x="0" y="0" width="516" height="226"/>
    <rect class="hot" data-k="sidewalk" tabindex="0" role="button" aria-label="Sidewalk" x="0" y="226" width="516" height="114"/>
    <rect class="hot" data-k="corner" tabindex="0" role="button" aria-label="Corner sidewalk" x="516" y="0" width="96" height="316"/>
    <path class="hot" data-k="street" tabindex="0" role="button" aria-label="Street" d="M0 356 H530 V560 H0 Z M600 356 H800 V560 H600 Z M624 0 H800 V356 H624 Z"/>
    <rect class="hot" data-k="ramp" tabindex="0" role="button" aria-label="Curb ramp" x="516" y="316" width="108" height="40"/>
    <rect class="hot" data-k="crosswalk" tabindex="0" role="button" aria-label="Crosswalk" x="530" y="356" width="70" height="204"/>
    <rect class="hot" data-k="bus" tabindex="0" role="button" aria-label="Bus stop" x="90" y="300" width="90" height="50"/>
    <rect class="hot" data-k="hydrant" tabindex="0" role="button" aria-label="Fire hydrant" x="386" y="304" width="52" height="52"/>
    <rect class="hot" data-k="drain" tabindex="0" role="button" aria-label="Storm drain" x="436" y="348" width="58" height="26"/>
  </g>` : ''}
</svg>`;
}
