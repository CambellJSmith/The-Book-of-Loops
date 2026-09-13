"use client"; // enables stable component-local SVG identifiers.

import { useId, type Ref } from "react"; // isolates SVG resources and exposes the export target.
import { Heart, Zap, Diamond, ImagePlus } from "lucide-react"; // provides functional card symbols.
import { ElementIcon } from "./element_icon"; // renders the monster's elemental symbol.
import { element_colors, type MonsterCard, type Move } from "@/lib/card_model"; // shares card data and colour rules.

function fit_font(text: string, maximum: number, available: number): number { // fits even unusually wide names into reserved card space.
  const units: number = Array.from(text).reduce((total: number, character: string) => total + (/[MWmw@%]/.test(character) ? 1 : /[ilIjtfr .,'!|]/.test(character) ? .4 : /[A-Z0-9]/.test(character) ? .76 : .68), 0); // estimates conservative glyph widths.
  return Math.min(maximum, available / Math.max(1, units)); // scales text without changing the card geometry.
}

export function CardPreview({ card, svg_ref }: { card: MonsterCard; svg_ref?: Ref<SVGSVGElement> }) { // shares one vector layout between preview and export.
  const uid: string = useId().replace(/[^a-zA-Z0-9]/g, ""); // avoids clipping collisions between previews.
  const color: string = element_colors[card.type]; // applies the selected elemental accent.
  const name: string = card.species_name || "your monster"; // makes an unfinished draft readable.
  const name_size: number = fit_font(name, 58, 645); // scales longer names into their reserved space.
  const id_width: number = Math.min(400, Math.max(170, (card.species_id.length + 1) * 14 + 35)); // gives longer species identifiers adequate badge space.
  const scale: number = Math.max(694 / card.art_width, 610 / card.art_height) * card.art_zoom; // fills the art window without stretching the source.
  const width: number = card.art_width * scale; // calculates the framed artwork width.
  const height: number = card.art_height * scale; // preserves the source aspect ratio.
  return ( // renders a self-contained card without external styles or fonts.
    <svg ref={svg_ref} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 1050" role="img" aria-label={`${name}, ${card.type}, health ${card.health}, speed ${card.speed}`} className="monster_card" fontFamily="Arial, Helvetica, sans-serif">
      <defs>
        <linearGradient id={`${uid}frame`} x1="0" y1="0" x2="1" y2="1"><stop stopColor={color} /><stop offset=".42" stopColor="#4a4847" /><stop offset="1" stopColor={color} /></linearGradient>
        <linearGradient id={`${uid}shade`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#171a1f" stopOpacity="0" /><stop offset=".45" stopColor="#171a1f" stopOpacity=".35" /><stop offset="1" stopColor="#171a1f" /></linearGradient>
        <clipPath id={`${uid}art`}><path d="M52 28H698L722 52V638H28V52Z" /></clipPath>
      </defs>
      <g id="card_frame"><path d="M35 3H715L747 35V1015L715 1047H35L3 1015V35Z" fill="#14171c" stroke={`url(#${uid}frame)`} strokeWidth="6" />
      <path d="M43 15H707L735 43V1007L707 1035H43L15 1007V43Z" fill="none" stroke={color} strokeOpacity=".23" strokeWidth="2" /></g>
      <g id="card_artwork">
      <path d="M52 28H698L722 52V638H28V52Z" fill="#242b34" />
      {card.art ? <image href={card.art} x={28 - (width - 694) * card.art_x / 100} y={28 - (height - 610) * card.art_y / 100} width={width} height={height} preserveAspectRatio="xMidYMid slice" clipPath={`url(#${uid}art)`} /> : <g color="#8993a1"><ImagePlus x="330" y="245" width="90" height="90" strokeWidth="1" /><text x="375" y="384" fill="#a8b0bc" textAnchor="middle" fontSize="25">add your artwork</text></g>}
      <rect x="28" y="430" width="694" height="220" fill={`url(#${uid}shade)`} />
      </g>
      <g id="card_species_id">
      <path d={`M48 48H${32 + id_width}L${48 + id_width} 64V100H48Z`} fill="#161a20" fillOpacity=".92" stroke={color} strokeOpacity=".35" />
      <text x="65" y="82" fill="#f0eae3" fontSize={fit_font(`#${card.species_id || "0000"}`, 22, id_width - 32)}>#{card.species_id || "0000"}</text>
      </g>
      <g id="card_type_badge">
      <path d="M558 48H684L702 66V110H558L540 92V66Z" fill={color} />
      <ElementIcon element={card.type} x="559" y="65" width="29" height="29" color="#191b20" strokeWidth="2" />
      <text x="601" y="87" fill="#191b20" fontWeight="700" fontSize="23">{card.type}</text>
      </g>
      <g id="card_species_name">
      <rect x="48" y="571" width="44" height="4" fill={color} />
      <text x="48" y="638" fill="#f7f1e8" fontSize={name_size} fontWeight="700">{name}</text>
      </g>
      <g id="card_base_stats">
      <path d="M48 674H702V766H48Z" fill="#24282e" />
      <path d="M48 674H702" stroke={color} strokeWidth="3" />
      <path d="M374 696V744" stroke="#4a4c50" />
      <Heart x="68" y="703" width="30" height="30" color={color} strokeWidth="1.7" />
      <text x="110" y="725" fill="#b8bcc4" fontSize="23">health</text>
      <text x="348" y="732" fill="#f5f0e9" textAnchor="end" fontSize={card.health > 999 ? 35 : 43} fontWeight="700">{card.health}</text>
      <Zap x="397" y="703" width="30" height="30" color={color} strokeWidth="1.7" />
      <text x="439" y="725" fill="#b8bcc4" fontSize="23">speed</text>
      <text x="679" y="732" fill="#f5f0e9" textAnchor="end" fontSize={card.speed > 999 ? 35 : 43} fontWeight="700">{card.speed}</text>
      </g>
      {card.moves.map((move: Move, index: number) => { // places both moves into a consistent layout.
        const y: number = 812 + index * 103; // separates the move rows.
        return <g key={index} id={`card_move_${index + 1}`}>
          <path d={`M48 ${y + 72}H702`} stroke="#383d44" />
          <path d={`M85 ${y - 18}L118 ${y + 15}L85 ${y + 48}L52 ${y + 15}Z`} fill={color} fillOpacity=".12" stroke={color} strokeOpacity=".65" />
          <text x="85" y={y + 25} textAnchor="middle" fill={color} fontSize={move.mana_cost > 99 ? 18 : 29} fontWeight="700">{move.mana_cost}</text>
          <text x="143" y={y + 10} fill="#f0ece6" fontSize={fit_font(move.name, 30, 395)} fontWeight="600">{move.name || `move ${index + 1}`}</text>
          <Diamond x="143" y={y + 28} width="15" height="15" color="#a6a8b2" />
          <text x="167" y={y + 42} fill="#a6a8b2" fontSize="19">{move.mana_cost} mana</text>
          <text x="696" y={y + 11} fill="#f0ece6" fontSize={move.damage > 999 ? 33 : 39} fontWeight="700" textAnchor="end">{move.damage}</text>
          <text x="696" y={y + 42} fill="#a6a8b2" fontSize="18" textAnchor="end">damage</text>
        </g>;
      })}
      <path d="M651 1006H677L686 1015H701" fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
}
