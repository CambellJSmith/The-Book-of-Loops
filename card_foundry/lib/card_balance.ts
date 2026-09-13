import { difficulties, elements, move_two_is_stronger, type Difficulty, type Element, type MonsterCard } from "@/lib/card_model"; // shares the canonical card contract and internal progression bands.

interface MoveBand { mana_cost: number; damage: number; } // describes one balanced attack slot inside an internal progression band.
const stat_totals: Record<Difficulty, number> = { easy: 150, medium: 190, hard: 235, extra_hard: 285, ultra: 340 }; // increases the combined health-and-speed budget at every internal progression step.
const move_bands: Record<Difficulty, readonly [MoveBand, MoveBand]> = { // gives later encounters both larger attacks and better damage efficiency while preserving the strong-second-move rule.
  easy: [{ mana_cost: 1, damage: 20 }, { mana_cost: 2, damage: 40 }], // keeps introductory encounters readable and forgiving.
  medium: [{ mana_cost: 1, damage: 30 }, { mana_cost: 3, damage: 70 }], // introduces a noticeably stronger finishing move.
  hard: [{ mana_cost: 2, damage: 55 }, { mana_cost: 3, damage: 90 }], // raises sustained damage for established encounters.
  extra_hard: [{ mana_cost: 2, damage: 70 }, { mana_cost: 4, damage: 125 }], // makes late encounters materially more dangerous.
  ultra: [{ mana_cost: 3, damage: 100 }, { mana_cost: 5, damage: 180 }], // reserves the largest normal-card attacks for endgame monsters.
};
const positive_terms: readonly (readonly [string, number])[] = [ // scores visual and anatomical cues that imply greater encounter threat.
  ["colossal", 10], ["giant", 6], ["huge", 6], ["massive", 6], ["fortress", 5], ["ancient", 4], ["guardian", 4], ["golem", 4], ["dragon", 6], ["basilisk", 6], ["tyrant", 5], ["rhinoceros", 4], ["lion", 3], ["walrus", 3], ["crocodilian", 4], ["sharklike", 4], ["scorpion", 4], ["raptor", 3], ["buffalo", 4], ["bear", 3], ["armoured", 3], ["armored", 3], ["heavy", 3], ["muscular", 3], ["strong", 3], ["broad shouldered", 2], ["basalt", 2], ["obsidian", 2], ["iron", 1], ["molten", 2], ["lava", 4], ["storm", 3], ["abyss", 3], ["whirlpool", 3], ["geyser", 3], ["furnace", 3], ["solar", 2], ["oracle", 3], ["knight", 2], ["sabre toothed", 4], ["carnivorous", 4], ["hornet", 3], ["serpent", 2],
];
const negative_terms: readonly (readonly [string, number])[] = [ // scores diminutive and gentle cues toward earlier encounter bands.
  ["thimble sized", -7], ["tiny", -6], ["small", -4], ["little", -4], ["delicate", -3], ["gentle", -3], ["cheerful", -3], ["playful", -3], ["friendly", -3], ["soft", -2], ["plump", -1], ["round", -1], ["curious", -1], ["sprite", -2], ["compact", -1],
];
const dangerous_move_terms: readonly (readonly [string, number])[] = [ // uses authored move language as a second signal of intended threat.
  ["crush", 4], ["eruption", 4], ["avalanche", 5], ["detonation", 5], ["inferno", 5], ["eclipse", 3], ["upheaval", 5], ["roar", 3], ["barrage", 4], ["charge", 2], ["torrent", 2], ["deluge", 4], ["quake", 4], ["blast", 4], ["cyclone", 4], ["stampede", 4], ["furnace", 4], ["blaze", 3], ["squall", 3], ["downpour", 3], ["gale", 2], ["ram", 2], ["pounce", 2], ["constrict", 3], ["sting", 2], ["slash", 2], ["beam", 2], ["surge", 1], ["rush", 1], ["wave", 1],
];
const gentle_move_terms: readonly (readonly [string, number])[] = [ // keeps harmless-sounding attack suites toward the lower end of a tied visual score.
  ["tap", -2], ["flick", -2], ["glint", -2], ["nudge", -2], ["hop", -1], ["clink", -1], ["dab", -1], ["bop", -1], ["whisk", -1], ["skip", -1], ["flutter", -1], ["step", -1],
];
function normalized_words(value: string): string { return ` ${value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim()} `; } // makes whole-word and multi-word threat matching predictable.
function weighted_score(text: string, terms: readonly (readonly [string, number])[]): number { // totals all authored threat cues present in one normalized description.
  const haystack: string = normalized_words(text); // normalizes punctuation and hyphenation once for the complete card text.
  return terms.reduce((total: number, [term, weight]: readonly [string, number]) => total + (haystack.includes(normalized_words(term)) ? weight : 0), 0); // adds each matching cue at most once.
}
function subject_text(card: MonsterCard): string { // isolates creature content from the repeated watercolor style boilerplate.
  const marker: string = "SUBJECT:"; // identifies the beginning of every generated creature description.
  const marker_index: number = card.art_prompt.indexOf(marker); // locates the authored subject when present.
  return marker_index >= 0 ? card.art_prompt.slice(marker_index + marker.length) : card.art_prompt; // falls back to the complete prompt for manually authored cards.
}
export function threat_score(card: MonsterCard): number { // estimates relative encounter threat from every monster's authored concept rather than its species number.
  if (card.species_id === "0400") return 1_000_000; // guarantees the final game card occupies the strongest internal progression slot.
  const concept: string = `${card.species_name} ${subject_text(card)}`; // combines the name with physical and magical creature cues.
  const moves: string = `${card.moves[0].name} ${card.moves[1].name}`; // combines both authored attack names for combat-intensity cues.
  return weighted_score(concept, positive_terms) + weighted_score(concept, negative_terms) + weighted_score(moves, dangerous_move_terms) + weighted_score(moves, gentle_move_terms); // produces one deterministic content-aware ranking score.
}
export function classify_standalone_difficulties(cards: readonly MonsterCard[]): Map<string, Difficulty> { // divides every element evenly across the internal progression bands.
  const result: Map<string, Difficulty> = new Map<string, Difficulty>(); // stores internal progression by durable card identity.
  for (const element of elements) { // classifies each element independently so every band keeps an even elemental mix.
    const ranked: MonsterCard[] = cards.filter((card: MonsterCard) => card.type === element).sort((left: MonsterCard, right: MonsterCard) => threat_score(left) - threat_score(right) || left.species_id.localeCompare(right.species_id)); // orders gentle concepts first and dangerous concepts last with a stable ID tiebreaker.
    if (ranked.length !== 80) throw new Error(`expected 80 ${element} monsters before internal progression classification`); // rejects incomplete sets before assigning arbitrary bands.
    ranked.forEach((card: MonsterCard, index: number) => result.set(card.id, difficulties[Math.min(difficulties.length - 1, Math.floor(index / 16))])); // assigns exactly sixteen cards of this element to each internal band.
  }
  return result; // returns all four hundred deterministic classifications.
}
function round_to_five(value: number): number { return Math.round(value / 5) * 5; } // keeps generated combat statistics easy to read at a glance.
function balanced_stats(card: MonsterCard, difficulty: Difficulty): { health: number; speed: number } { // scales total power while preserving each monster's tank-versus-speed identity.
  const original_total: number = Math.max(1, card.health + card.speed); // avoids division by zero for malformed historical source values.
  const health_ratio: number = card.health / original_total; // captures the authored durability share independently from total power.
  const target_total: number = stat_totals[difficulty]; // selects the combined statistic budget for this internal encounter band.
  const health: number = Math.max(20, Math.min(target_total - 20, round_to_five(target_total * health_ratio))); // scales durability while retaining at least twenty points for speed.
  return { health, speed: target_total - health }; // preserves the exact internal budget after health rounding.
}
function final_boss_prompt(card: MonsterCard): string { // replaces the modest original Duskervet concept with a true final-boss silhouette.
  const style: string = card.art_prompt.split("\n\nSUBJECT:")[0].trim(); // preserves the established shared watercolor style verbatim.
  const subject: string = "SUBJECT: duskervet, an original dark-type final-boss monster. Depict a colossal four-legged sovereign formed from layered smoky indigo fur and articulated black-violet shadow armour, with six sweeping silver whisker-horns, a crown of suspended eclipse rings, a luminous violet core set deep in its chest, polished obsidian claws and nine vast fan-shaped shadow tails arcing behind it like a broken celestial wheel. Each tail carries fine silver runic seams and starless black eyespots, while a mantle of slow violet darkness rises behind its shoulders into a regal silhouette. Present Duskervet planted in a dominant, imposing stance with its full anatomy clearly readable, immense scale communicated through monumental proportions, broad weight-bearing limbs and controlled supernatural presence. Keep every tail individually legible and make the crown, chest core, whisker-horns and central face the unmistakable focal hierarchy. Render the creature as the singular climactic opponent of the world, with refined watercolor material separation, a soft grounded contact shadow and generous clean off-white paper surrounding the complete silhouette."; // defines the canonical climactic creature while staying compatible with the existing art pipeline.
  return style ? `${style}\n\n${subject}` : subject; // keeps custom style prefixes when the source prompt contains one.
}
export function balance_standalone_cards(cards: readonly MonsterCard[]): MonsterCard[] { // applies classification and combat scaling to the canonical four-hundred-card set.
  const classifications: Map<string, Difficulty> = classify_standalone_difficulties(cards); // establishes content-aware internal bands before changing any statistics.
  const balanced: MonsterCard[] = cards.map((card: MonsterCard) => { // returns fresh records without mutating the imported seed objects.
    const difficulty: Difficulty = classifications.get(card.id) ?? "easy"; // reads the deterministic internal band for this canonical identity.
    if (card.species_id === "0400") return { ...card, difficulty: "ultra", is_final_boss: true, art_prompt: final_boss_prompt(card), health: 540, speed: 160, moves: [{ name: "voidwhisker rend", mana_cost: 4, damage: 180 }, { name: "last eclipse", mana_cost: 7, damage: 360 }] }; // gives Duskervet a unique high-cost, high-damage move pair while keeping Move 2 stronger.
    const stats: { health: number; speed: number } = balanced_stats(card, difficulty); // scales the original combat archetype into its assigned internal band.
    const attacks: readonly [MoveBand, MoveBand] = move_bands[difficulty]; // selects the two standard attack profiles for the band.
    return { ...card, difficulty, is_final_boss: false, health: stats.health, speed: stats.speed, moves: [{ ...card.moves[0], mana_cost: attacks[0].mana_cost, damage: attacks[0].damage }, { ...card.moves[1], mana_cost: attacks[1].mana_cost, damage: attacks[1].damage }] }; // preserves names and artwork while replacing only progression-sensitive combat values.
  });
  const invalid: MonsterCard | undefined = balanced.find((card: MonsterCard) => !move_two_is_stronger(card.moves)); // verifies the turn-based Mana design survives every canonical balancing path.
  if (invalid) throw new Error(`move 2 must cost more mana and deal more damage than move 1 for species ${invalid.species_id}`); // prevents a future balance-table edit from creating an inverted move pair.
  return balanced; // returns only a canonically ordered move set.
}

export function difficulty_counts(cards: readonly MonsterCard[]): Record<Difficulty, number> { // summarizes internal progression distribution for validation logic.
  return cards.reduce((counts: Record<Difficulty, number>, card: MonsterCard) => ({ ...counts, [card.difficulty]: counts[card.difficulty] + 1 }), { easy: 0, medium: 0, hard: 0, extra_hard: 0, ultra: 0 }); // counts every card exactly once by its stored internal band.
}

export function element_difficulty_count(cards: readonly MonsterCard[], element: Element, difficulty: Difficulty): number { return cards.filter((card: MonsterCard) => card.type === element && card.difficulty === difficulty).length; } // supports strict internal distribution validation without exposing progression metadata to players.
