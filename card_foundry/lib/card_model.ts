import { z } from "zod"; // validates cards at the application boundary.

export const elements = ["fire", "water", "nature", "light", "dark"] as const; // defines the available monster types.
export type Element = (typeof elements)[number]; // restricts type selections to the supported elements.
export const element_colors: Record<Element, string> = { fire: "#f29255", water: "#60bff5", nature: "#91c974", light: "#ead58a", dark: "#b49bea" }; // gives every element a distinct accent.
const stat_schema = z.number().int().min(0).max(9999); // bounds whole-number card statistics.
const move_schema = z.object({ name: z.string().trim().min(1, "give each move a name").max(36), mana_cost: stat_schema, damage: stat_schema }); // describes one monster move.
export const card_schema = z.object({ // defines the complete monster record.
  id: z.string().uuid(), // identifies the saved record independently from its species.
  species_id: z.string().trim().min(1, "enter a species id").max(20), // preserves leading zeros and custom numbering.
  species_name: z.string().trim().min(1, "enter a species name").max(40), // labels the monster on the card.
  type: z.enum(elements), // selects the card palette and elemental icon.
  art: z.string().regex(/^(|\/sample_art\.webp|\/api\/art\/[a-f0-9-]{36})$/, "choose an uploaded image"), // permits only artwork hosted by this tool.
  art_prompt: z.string().max(6000).default(""), // preserves an optional self-contained artwork brief on every card.
  art_width: z.number().int().min(1).max(12000), // retains the original image width for precise framing.
  art_height: z.number().int().min(1).max(12000), // retains the original image height for precise framing.
  art_zoom: z.number().min(1).max(3), // adjusts the artwork magnification.
  art_x: z.number().min(0).max(100), // positions the artwork horizontally.
  art_y: z.number().min(0).max(100), // positions the artwork vertically.
  health: stat_schema, // describes monster durability.
  speed: stat_schema, // describes monster initiative.
  moves: z.tuple([move_schema, move_schema]), // requires exactly two moves.
  revision: z.number().int().min(0), // prevents stale saves from overwriting newer changes.
});
export type MonsterCard = z.infer<typeof card_schema>; // shares the checked card shape across the editor and server.
export type Move = MonsterCard["moves"][number]; // describes an individual editable move.
export const example_card: MonsterCard = { // supplies an editable example without inserting records.
  id: "00000000-0000-4000-8000-000000000001", species_id: "0001", species_name: "cindrel", type: "fire", // establishes the sample species.
  art_prompt: "", art: "/sample_art.webp", art_width: 1122, art_height: 1402, art_zoom: 1, art_x: 50, art_y: 35, // frames the original example artwork.
  health: 120, speed: 45, revision: 0, // sets the example's editable statistics.
  moves: [{ name: "ember flick", mana_cost: 1, damage: 20 }, { name: "flare spiral", mana_cost: 3, damage: 60 }], // demonstrates the two move slots.
};
export function next_species_id(cards: MonsterCard[]): string { // finds an unused sequential species number.
  const taken: Set<string> = new Set(cards.map((card: MonsterCard) => card.species_id)); // collects existing identifiers.
  let index: number = 1; // starts the search for an available identifier.
  while (taken.has(String(index).padStart(4, "0"))) index += 1; // skips identifiers already in use.
  return String(index).padStart(4, "0"); // maintains readable leading zeros.
}
export function blank_card(cards: MonsterCard[]): MonsterCard { // makes a fresh unsaved monster.
  return { ...example_card, id: crypto.randomUUID(), species_id: next_species_id(cards), species_name: "", art: "", art_prompt: "", health: 100, speed: 50, moves: [{ name: "", mana_cost: 1, damage: 10 }, { name: "", mana_cost: 2, damage: 30 }] }; // separates new card data from the sample.
}
