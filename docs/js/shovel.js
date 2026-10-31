/* "Down to the pavement" illustration: one street corner that changes as the reader scrolls the five steps.
   main.js sets svg[data-s] to 0–5. Layers with class onN are visible in step N (CSS in style.css, "shovel scene").
   Each step plays one short animation when it starts. Every animated element's resting state is its end state,
   so with prefers-reduced-motion (animations off) the reader still sees the finished picture for each step. */

// Small deterministic random, so the snow looks the same on every load.
function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646; }

// A rectangle with lumpy edges, drawn as one path: looks like a snow mass rather than a box.
function lumpy(x, y, w, h, seed, amp = 7, step = 34) {
  const r = rng(seed);
  const pts = [];
  const edge = (x0, y0, x1, y1, nx, ny) => {
    const len = Math.hypot(x1 - x0, y1 - y0);
    const n = Math.max(1, Math.round(len / step));
    for (let i = 0; i < n; i++) {
      const t0 = i / n; const t1 = (i + 1) / n;
      const mx = x0 + (x1 - x0) * (t0 + t1) / 2; const my = y0 + (y1 - y0) * (t0 + t1) / 2;
      const a = amp * (0.4 + r());
      pts.push(`Q${(mx + nx * a).toFixed(1)} ${(my + ny * a).toFixed(1)} ${(x0 + (x1 - x0) * t1).toFixed(1)} ${(y0 + (y1 - y0) * t1).toFixed(1)}`);
    }
  };
  edge(x, y, x + w, y, 0, -1);
  edge(x + w, y, x + w, y + h, 1, 0);
  edge(x + w, y + h, x, y + h, 0, 1);
  edge(x, y + h, x, y, -1, 0);
  return `M${x} ${y} ${pts.join(' ')}Z`;
}

// Plow timing (step 5): the blade's front edge passes x at this many seconds after the step starts.
const PLOW_S = 2.6; const PLOW_FROM = -280; const PLOW_TO = 1080; const BLADE = 202;
const plowAt = (x) => ((x - (PLOW_FROM + BLADE)) / (PLOW_TO - PLOW_FROM)) * PLOW_S;

export function shovelScene(id) {
  const r = rng(7);
  const SW = '#5E6C7B'; // sidewalk concrete under snow
  const BARE = '#6E7C8C'; // freshly cleared pavement
  const SNOW = '#FFFFFF'; const SHADE = '#B9CBDD'; const SOFT = '#E7EEF5';

  const windows = [];
  for (let row = 0; row < 2; row++) for (let c = 0; c < 6; c++) {
    if (row === 1 && (c === 2 || c === 3)) continue;
    windows.push(`<rect x="${34 + c * 78}" y="${30 + row * 76}" width="40" height="44" rx="3"/>`);
  }

  // Snow mass over both sidewalks (and the ramp, until step 3).
  const snowShapes = [lumpy(-12, 222, 628, 126, 11), lumpy(510, -14, 108, 250, 23)];
  const snow = snowShapes.map((d) => `<path d="${d}" fill="${SHADE}" transform="translate(0 6)"/>`).join('')
    + snowShapes.map((d) => `<path d="${d}" fill="${SNOW}"/>`).join('')
    + [[90, 300, 70, 12], [300, 248, 90, 10], [430, 318, 60, 9], [560, 90, 14, 46], [585, 200, 10, 30], [200, 330, 50, 7]]
      .map(([cx, cy, rx, ry]) => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${SOFT}"/>`).join('');

  const joints = (horiz) => Array.from({ length: horiz ? 9 : 4 }, (_, i) => horiz
    ? `<path d="M${64 * (i + 1)} 256 V316" stroke="#5B6979" stroke-width="2"/>`
    : `<path d="M535 ${64 * (i + 1) - 8} H595" stroke="#5B6979" stroke-width="2"/>`).join('');

  const flakes = Array.from({ length: 34 }, () => {
    const x = Math.round(r() * 790); const y = Math.round(r() * 520); const s = (2 + r() * 3).toFixed(1);
    return `<circle class="flake" cx="${x}" cy="${y}" r="${s}" fill="#fff" style="animation-delay:${(r() * 0.7).toFixed(2)}s"/>`;
  }).join('');

  // Ice patches (step 4) and the sand thrown on them.
  const ice = [[468, 290, 58, 18], [300, 280, 40, 13], [565, 334, 24, 11]];
  const sand = ice.flatMap(([cx, cy, rx, ry]) => Array.from({ length: Math.round(rx / 2.4) }, () => {
    const a = r() * Math.PI * 2; const d = Math.sqrt(r()) * 0.85;
    return `<circle cx="${(cx + Math.cos(a) * rx * d).toFixed(1)}" cy="${(cy + Math.sin(a) * ry * d).toFixed(1)}" r="${(2 + r() * 1.6).toFixed(1)}" fill="${r() > 0.5 ? '#C9A36A' : '#8E6B3E'}"/>`;
  })).join('');

  // Plow berm along the curb (step 5). Each lump appears as the blade passes it.
  const berm = [];
  for (let x = 14; x < 520; x += 38) {
    const cx = x + Math.round(r() * 10); const ry = 14 + Math.round(r() * 6);
    berm.push(`<ellipse class="lump" cx="${cx}" cy="${352 + Math.round(r() * 6)}" rx="28" ry="${ry}" fill="${SNOW}" style="transform-origin:${cx}px 352px;animation-delay:${plowAt(cx).toFixed(2)}s"/>`);
  }
  const heap = [[548, 344, 40, 26], [585, 350, 36, 24], [566, 372, 44, 22], [600, 330, 20, 18]]
    .map(([cx, cy, rx, ry]) => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${SNOW}"/>`).join('');

  return `<svg id="${id}" class="scene" viewBox="0 0 800 560" data-s="0" role="img" aria-label="Illustration of a street corner after a snowstorm. It changes with each step: snow covers the sidewalks, a 36-inch path is shoveled to bare pavement, the curb ramp is opened to the crosswalk, ice is sanded, and a plow buries the ramp, which is cleared again.">
  <defs><clipPath id="${id}-clip"><rect width="800" height="560"/></clipPath></defs>
  <g clip-path="url(#${id}-clip)">
  <rect width="800" height="560" fill="#10243A"/>
  <!-- building -->
  <rect x="0" y="0" width="516" height="226" fill="#2B5482"/>
  <g fill="#F4C95D" opacity=".9">${windows.join('')}</g>
  <rect x="226" y="168" width="64" height="58" rx="3" fill="#10243A"/>
  <rect x="454" y="150" width="10" height="74" fill="#A9C4E4"/><rect x="448" y="218" width="22" height="8" rx="2" fill="#A9C4E4"/>
  <!-- sidewalks, curb, streets -->
  <rect x="0" y="226" width="612" height="114" fill="${SW}"/>
  <rect x="516" y="0" width="96" height="340" fill="${SW}"/>
  <rect x="0" y="340" width="624" height="12" fill="#9AA8B6"/>
  <rect x="612" y="0" width="12" height="352" fill="#9AA8B6"/>
  <g fill="#fff">${Array.from({ length: 8 }, (_, i) => `<rect x="535" y="${362 + i * 25}" width="60" height="13"/>`).join('')}</g>
  <path d="M0 474 H505" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <path d="M712 0 V336" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <path d="M640 474 H800" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>

  <!-- snow on the sidewalks -->
  <g>${snow}</g>

  <!-- step 1: snow stops, clock starts, both sidewalks are yours -->
  <g class="sv on1">${flakes}</g>
  <path class="sv on1 duty" d="M0 222 H512 V-4 M616 -4 V346 H0" fill="none" stroke="#FF8A3D" stroke-width="6" stroke-dasharray="14 12" stroke-linecap="round"/>
  <g class="sv on1 clock">
    <circle cx="712" cy="118" r="54" fill="#EEF3F7" stroke="#10243A" stroke-width="5"/>
    <circle class="arc" cx="712" cy="118" r="38" fill="none" stroke="#FF8A3D" stroke-width="16" pathLength="100" stroke-dasharray="50 100" transform="rotate(-90 712 118)"/>
    <path class="hand" d="M712 118 V78" stroke="#10243A" stroke-width="6" stroke-linecap="round"/>
    <circle cx="712" cy="118" r="6" fill="#10243A"/>
    <text x="712" y="210" text-anchor="middle" class="cap" font-size="34" fill="#fff">6 HRS</text>
  </g>

  <!-- step 2+: the shoveled path, bare pavement -->
  <g class="sv on2 on3 on4 on5">
    <rect x="0" y="256" width="595" height="60" fill="${BARE}"/>${joints(true)}
    <rect x="535" y="0" width="60" height="256" fill="${BARE}"/>${joints(false)}
    <rect x="0" y="256" width="535" height="6" fill="#4F5C6A" opacity=".55"/>
    <rect x="535" y="0" width="6" height="262" fill="#4F5C6A" opacity=".55"/>
    <rect class="cover coverA" x="0" y="252" width="595" height="68" fill="${SNOW}"/>
    <rect class="cover coverB" x="531" y="0" width="68" height="256" fill="${SNOW}"/>
  </g>
  <g class="sv on2 dim">
    <path d="M150 262 V310 M138 262 H162 M138 310 H162" stroke="#FF8A3D" stroke-width="5" stroke-linecap="round"/>
    <text x="174" y="298" class="cap" font-size="32" fill="#fff">36 IN</text>
  </g>
  <g class="sv on2"><g class="shovel"><circle r="26" fill="#FF8A3D" stroke="#10243A" stroke-width="4"/><use href="#i-shovel" x="-17" y="-17" width="34" height="34" fill="none" stroke="#10243A" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g></g>

  <!-- step 3: ramp opened to the crosswalk -->
  <!-- step 3+: the curb ramp, shoveled open (a snow cover wipes off it in step 3) -->
  <g class="sv on3 on4 on5">
    <path d="M519 316 H535 V352 Z M611 316 H595 V352 Z" fill="#7D8A98"/>
    <rect x="535" y="316" width="60" height="26" fill="#8C99A7"/>
    <rect x="535" y="338" width="60" height="14" fill="#F4C95D"/>
    <g fill="#C79A1F">${Array.from({ length: 10 }, (_, i) => `<circle cx="${541 + (i % 5) * 12}" cy="${342 + Math.floor(i / 5) * 6}" r="1.8"/>`).join('')}</g>
  </g>

  <rect class="sv on3 cover rampcover" x="526" y="312" width="78" height="46" fill="${SNOW}"/>
  <path class="sv on3 route" d="M40 286 H565 V548" fill="none" stroke="#FF8A3D" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="0 17"/>
  <g class="sv on3"><g class="walker">
    <circle r="24" fill="#FF8A3D" stroke="#10243A" stroke-width="4"/>
    <g fill="none" stroke="#10243A" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="-1" cy="-13" r="3" fill="#10243A" stroke="none"/><path d="M-2 -7 V3 H8 L11 12"/><path d="M-6 -2 A9 9 0 1 0 6 10"/></g>
  </g></g>

  <!-- step 4: ice refroze; sand it -->
  <g class="sv on4">
    <path class="drip" d="M459 228 Q462 246 466 272" stroke="#A9C4E4" stroke-width="4" stroke-dasharray="5 6" fill="none"/>
    ${ice.map(([cx, cy, rx, ry], i) => `<ellipse class="icep" cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#CFE8FF" stroke="#fff" stroke-width="2" style="transform-origin:${cx}px ${cy}px;animation-delay:${(i * 0.2).toFixed(1)}s"/>`).join('')}
    <g class="glint" stroke="#fff" stroke-width="3" stroke-linecap="round"><path d="M482 282 l0 12 M476 288 h12"/><path d="M296 274 l0 10 M291 279 h10"/></g>
    <g class="sand">${sand}</g>
  </g>

  <!-- step 5: plow buries the ramp; clear it again -->
  <g class="sv on5">
    ${berm.join('')}
    <g class="heap">${heap}</g>
    <g class="plow">
      <rect x="18" y="368" width="26" height="9" fill="#0A1929"/><rect x="18" y="437" width="26" height="9" fill="#0A1929"/>
      <rect x="112" y="368" width="26" height="9" fill="#0A1929"/><rect x="112" y="437" width="26" height="9" fill="#0A1929"/>
      <rect x="0" y="374" width="124" height="66" rx="6" fill="#FF8A3D"/>
      <path d="M14 384 H110 M14 398 H110 M14 412 H110 M14 426 H110" stroke="#D96A22" stroke-width="3"/>
      <rect x="128" y="378" width="44" height="58" rx="7" fill="#FF8A3D"/>
      <rect x="156" y="384" width="11" height="46" rx="2" fill="#10243A"/>
      <circle class="beacon" cx="142" cy="407" r="7" fill="#FFD34D"/>
      <path d="M180 398 H190 M180 416 H190" stroke="#9AA8B6" stroke-width="5"/>
      <path d="M186 360 L196 360 L${BLADE} 452 L${BLADE - 10} 452 Z" fill="#C9D6E3" stroke="#10243A" stroke-width="2"/>
      <g fill="#fff"><circle cx="190" cy="352" r="5"/><circle cx="178" cy="345" r="4"/><circle cx="196" cy="342" r="3"/></g>
    </g>
    <g class="shovel2" transform="translate(565 300)"><circle r="26" fill="#FF8A3D" stroke="#10243A" stroke-width="4"/><use href="#i-shovel" x="-17" y="-17" width="34" height="34" fill="none" stroke="#10243A" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g>
  </g>
  </g>
</svg>`;
}
