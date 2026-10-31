/* Street-corner illustration for the "Who clears this?" map. With hot=true it adds tappable hotspots.
   The step-by-step "Down to the pavement" picture is its own drawing in shovel.js. */
export function corner(id, hot){
  const P='#5E6C7B';
    const stripesH=[0,1,2,3,4,5].map(i=>`<rect x="462" y="${424+i*22}" width="76" height="12" fill="#fff"/>`).join('');
  const stripesV=[0,1,2,3,4,5,6,7,8,9].map(i=>`<rect x="${566+i*23}" y="312" width="12" height="86" fill="#fff"/>`).join('');
  return `<svg id="${id}" viewBox="0 0 800 560" role="img" aria-label="Top view of a Somerville street corner: a building, the sidewalks along two streets, curb ramps, crosswalks, a bus stop, a hydrant and a storm drain">
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
