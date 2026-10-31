/* Street-corner illustration, shared by the step-by-step (no hotspots) and the "Who clears this?" map (with hotspots).
   Layers with class L-* are shown per step through CSS rules on svg[data-s]. */
export function corner(id, hot){
  const P='#5E6C7B';
  const snowBumps=(x,y,w,h)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="10" fill="#fff"/>`;
  const stripesH=[0,1,2,3,4,5].map(i=>`<rect x="462" y="${424+i*22}" width="76" height="12" fill="#fff"/>`).join('');
  const stripesV=[0,1,2,3,4,5,6,7,8,9].map(i=>`<rect x="${566+i*23}" y="312" width="12" height="86" fill="#fff"/>`).join('');
  return `<svg id="${id}" viewBox="0 0 800 560" data-s="${hot?0:1}" role="img" aria-label="Top view of a Somerville street corner: a building, the sidewalks along two streets, curb ramps, crosswalks, a bus stop, a hydrant and a storm drain">
  <rect width="800" height="560" fill="#DCE8F5"/>
  <rect x="0" y="0" width="450" height="300" fill="#2B5482"/>
  <g fill="#F4C95D" opacity=".9"><rect x="40" y="40" width="44" height="44"/><rect x="120" y="40" width="44" height="44"/><rect x="200" y="40" width="44" height="44"/><rect x="280" y="40" width="44" height="44"/><rect x="360" y="40" width="44" height="44"/><rect x="40" y="130" width="44" height="44"/><rect x="200" y="130" width="44" height="44"/><rect x="360" y="130" width="44" height="44"/></g>
  <rect x="190" y="236" width="70" height="64" fill="#10243A"/>
  <text x="225" y="222" text-anchor="middle" class="cap" font-size="26" fill="#fff">BUILDING</text>
  <rect x="436" y="230" width="10" height="72" fill="#A9C4E4"/>
  <rect x="0" y="310" width="540" height="90" fill="${P}"/>
  <rect x="460" y="0" width="80" height="400" fill="${P}"/>
  <rect x="0" y="400" width="460" height="12" fill="#9AA8B6"/>
  <rect x="540" y="0" width="12" height="310" fill="#9AA8B6"/>
  <rect x="460" y="400" width="80" height="12" fill="#F4C95D"/>
  <rect x="540" y="310" width="12" height="90" fill="#F4C95D"/>
  <rect x="540" y="400" width="12" height="12" fill="#9AA8B6"/>
  <rect x="0" y="412" width="800" height="148" fill="#10243A"/>
  <rect x="552" y="0" width="248" height="560" fill="#10243A"/>
  <g>${stripesH}${stripesV}</g>
  <path d="M600 486 L780 486" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <path d="M676 20 L676 290" stroke="#F4C95D" stroke-width="5" stroke-dasharray="26 18"/>
  <rect x="400" y="414" width="44" height="12" rx="2" fill="#2E3D4F"/><path d="M408 416v8M416 416v8M424 416v8M432 416v8" stroke="#8C9BAB" stroke-width="2"/>
  <circle cx="370" cy="388" r="9" fill="#D9412B"/><rect x="364" y="374" width="12" height="7" rx="2" fill="#D9412B"/>
  <rect x="146" y="350" width="6" height="48" fill="#10243A"/><rect x="128" y="330" width="42" height="26" rx="5" fill="#FF8A3D"/><text x="149" y="349" text-anchor="middle" class="cap" font-size="15" fill="#10243A">BUS</text>
  <rect x="60" y="316" width="70" height="14" rx="4" fill="#A9C4E4" opacity=".8"/>

  <!-- step layers -->
  <g class="L L-snow">${snowBumps(0,306,545,104)}${snowBumps(456,0,90,410)}${snowBumps(452,396,104,20)}${snowBumps(536,304,22,100)}
    <ellipse cx="120" cy="330" rx="60" ry="14" fill="#F2F6FA"/><ellipse cx="330" cy="380" rx="80" ry="12" fill="#F2F6FA"/><ellipse cx="500" cy="160" rx="18" ry="60" fill="#F2F6FA"/>
    <text x="230" y="366" text-anchor="middle" class="cap" font-size="30" fill="#47607C">BURIED SIDEWALK</text></g>
  <g class="L L-banks"><rect x="0" y="306" width="460" height="24" rx="8" fill="#fff"/><rect x="0" y="384" width="350" height="22" rx="8" fill="#fff"/><rect x="390" y="384" width="70" height="22" rx="8" fill="#fff"/>
    <rect x="456" y="0" width="22" height="310" rx="8" fill="#fff"/><rect x="522" y="0" width="24" height="306" rx="8" fill="#fff"/></g>
  <g class="L L-rampsnow">${snowBumps(452,380,100,34)}${snowBumps(520,302,40,104)}</g>
  <g class="L L-bankfull"><rect x="0" y="412" width="552" height="24" rx="10" fill="#fff"/><rect x="552" y="0" width="24" height="436" rx="10" fill="#fff"/></g>
  <g class="L L-bankopen"><rect x="0" y="412" width="458" height="24" rx="10" fill="#fff"/><rect x="552" y="0" width="24" height="306" rx="10" fill="#fff"/><rect x="552" y="404" width="24" height="32" rx="10" fill="#fff"/></g>
  <g class="L L-dim"><path d="M250 334 L250 380 M238 334 L262 334 M238 380 L262 380" stroke="#FF8A3D" stroke-width="5" stroke-linecap="round"/><text x="274" y="368" class="cap" font-size="34" fill="#fff">36 INCHES</text></g>
  <g class="L L-arrow"><path d="M30 357 L440 357 L500 357 L500 520" fill="none" stroke="#FF8A3D" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="2 14"/><path d="M486 504 L500 524 L514 504" fill="none" stroke="#FF8A3D" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><text x="60" y="345" class="cap" font-size="26" fill="#fff">CLEAR TO THE CROSSWALK</text></g>
  <g class="L L-ice"><path d="M441 302 L441 336" stroke="#A9C4E4" stroke-width="5" stroke-dasharray="6 6"/><ellipse cx="420" cy="356" rx="70" ry="18" fill="#BFE3FF" opacity=".85"/><ellipse cx="300" cy="350" rx="50" ry="12" fill="#BFE3FF" opacity=".75"/><ellipse cx="500" cy="300" rx="14" ry="40" fill="#BFE3FF" opacity=".75"/>
    <path d="M410 350l8-6M300 346l6 5M500 290l-5 7" stroke="#fff" stroke-width="3"/><text x="40" y="368" class="cap" font-size="30" fill="#fff">ICE REFROZE OVERNIGHT</text></g>
  <g class="L L-pile"><ellipse cx="500" cy="410" rx="62" ry="30" fill="#fff"/><ellipse cx="548" cy="356" rx="22" ry="54" fill="#fff"/><text x="280" y="368" class="cap" font-size="30" fill="#fff">RAMP BURIED</text></g>
  <g class="L L-plow"><rect x="300" y="456" width="96" height="48" rx="8" fill="#FF8A3D"/><rect x="360" y="462" width="30" height="20" rx="3" fill="#10243A"/><path d="M296 448 L280 512" stroke="#C9D6E3" stroke-width="10" stroke-linecap="round"/><circle cx="320" cy="508" r="7" fill="#0A1929"/><circle cx="378" cy="508" r="7" fill="#0A1929"/></g>
  ${hot?`
  <g>
    <rect class="hot" data-k="sidewalk" tabindex="0" role="button" aria-label="Sidewalk" x="0" y="310" width="456" height="88"/>
    <rect class="hot" data-k="corner" tabindex="0" role="button" aria-label="Corner sidewalk" x="460" y="0" width="80" height="398"/>
    <rect class="hot" data-k="ramp" tabindex="0" role="button" aria-label="Curb ramp" x="454" y="394" width="104" height="26"/>
    <rect class="hot" data-k="crosswalk" tabindex="0" role="button" aria-label="Crosswalk" x="458" y="420" width="84" height="140"/>
    <rect class="hot" data-k="street" tabindex="0" role="button" aria-label="Street" x="580" y="420" width="220" height="140"/>
    <rect class="hot" data-k="bus" tabindex="0" role="button" aria-label="Bus stop" x="56" y="312" width="124" height="88"/>
    <rect class="hot" data-k="hydrant" tabindex="0" role="button" aria-label="Fire hydrant" x="352" y="368" width="36" height="34"/>
    <rect class="hot" data-k="drain" tabindex="0" role="button" aria-label="Storm drain" x="396" y="410" width="52" height="22"/>
    <rect class="hot" data-k="building" tabindex="0" role="button" aria-label="Building, stairs and exits" x="0" y="0" width="450" height="300"/>
  </g>`:''}
</svg>`;
}
