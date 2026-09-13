import { card_schema, type Difficulty, type Element, type MonsterCard, type Move } from "@/lib/card_model"; // shares validated monster fields with the editor.
import { embed_artwork, type EmbeddedArtwork } from "./artwork"; // makes every referenced image portable.
import { download_blob } from "./download"; // invokes the standard file download action.

export interface ObjectArtwork { asset_id: string; width: number; height: number; zoom: number; position_x: number; position_y: number; } // retains both artwork identity and card framing.
export interface CardObject { species_id: string; species_name: string; type: Element; difficulty: Difficulty; is_final_boss: boolean; art: ObjectArtwork | null; art_prompt: string; health: number; speed: number; moves: [Move, Move]; } // exports program-friendly progression and card fields without editor-only database state.
export interface CardObjectDocument { format: "card_foundry"; schema_version: 2; cards: CardObject[]; assets: Record<string, EmbeddedArtwork>; } // versions the portable file format after adding encounter progression metadata.
export type ExportProgress = (completed: number, total: number) => void; // reports progress while embedding a saved collection.
export type ArtworkLoader = (source: string) => Promise<EmbeddedArtwork>; // isolates image loading from the portable object conversion.

export async function create_card_objects(records: readonly MonsterCard[], progress?: ExportProgress, load_artwork: ArtworkLoader = embed_artwork): Promise<CardObjectDocument> { // converts complete cards into an independent, versioned object document.
  if (!records.length) throw new Error("save a card before exporting your collection"); // avoids ambiguous empty downloads.
  const cards: MonsterCard[] = records.map((record: MonsterCard) => card_schema.parse(record)); // validates and snapshots the entire selection before reading artwork.
  const sources: Map<string, string> = new Map(); // deduplicates shared artwork across exported cards.
  const assets: Record<string, EmbeddedArtwork> = {}; // stores image bytes once per unique artwork reference.
  for (const card of cards) if (card.art && !sources.has(card.art)) sources.set(card.art, `art_${String(sources.size + 1).padStart(4, "0")}`); // assigns stable document-local asset keys without manual image naming.
  progress?.(0, sources.size); // exposes the total number of images before work begins.
  let completed: number = 0; // tracks embedded artwork progress.
  for (const [source, asset_id] of sources) { // bounds image-loading memory by processing one asset at a time.
    assets[asset_id] = await load_artwork(source); // includes actual image bytes instead of inaccessible private URLs.
    completed += 1; progress?.(completed, sources.size); // advances progress only after an image is included.
  }
  const objects: CardObject[] = cards.map((card: MonsterCard) => ({ // preserves game data independently from the current editor implementation.
    species_id: card.species_id, species_name: card.species_name, type: card.type, difficulty: card.difficulty, is_final_boss: card.is_final_boss, // keeps identifiers, element and encounter progression explicit.
    art: card.art ? { asset_id: sources.get(card.art)!, width: card.art_width, height: card.art_height, zoom: card.art_zoom, position_x: card.art_x, position_y: card.art_y } : null, // retains artwork framing without inventing missing images.
    art_prompt: card.art_prompt, // keeps the future generation brief available to other programs.
    health: card.health, speed: card.speed, moves: [{ ...card.moves[0] }, { ...card.moves[1] }], // preserves numeric statistics and complete independent move objects.
  }));
  return { format: "card_foundry", schema_version: 2, cards: objects, assets }; // returns a JSON-compatible object with progression metadata and all referenced artwork.
}
export async function export_card_objects(records: readonly MonsterCard[], filename: string, progress?: ExportProgress): Promise<number> { // downloads one card or the saved collection using the same file format.
  const document: CardObjectDocument = await create_card_objects(records, progress); // resolves the complete portable document before downloading.
  const pieces: BlobPart[] = [`{\n  "format": "card_foundry",\n  "schema_version": 2,\n  "cards": `, JSON.stringify(document.cards, null, 2), `,\n  "assets": {`]; // avoids building one enormous combined base64 string.
  const entries: [string, EmbeddedArtwork][] = Object.entries(document.assets); // preserves the shared asset ordering.
  entries.forEach(([asset_id, artwork]: [string, EmbeddedArtwork], index: number): void => { // serializes one embedded asset at a time.
    pieces.push(`${index ? "," : ""}\n    ${JSON.stringify(asset_id)}: `, JSON.stringify(artwork)); // keeps asset keys and binary payloads valid JSON.
  });
  pieces.push("\n  }\n}\n"); // completes the portable document.
  download_blob(new Blob(pieces, { type: "application/json;charset=utf-8" }), filename); // downloads plain JSON that other programs can parse.
  return document.cards.length; // reports the number of exported records.
}
