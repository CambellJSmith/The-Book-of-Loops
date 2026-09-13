import source_cards from "@/data/standalone_400.json"; // uses the same authored balance as new collection installations.
import { database } from "./storage"; // shares the existing durable storage boundary.

const balance_id: string = "standalone_400_balance_v2"; // prevents later visits from undoing edits made after this update.
export async function apply_card_balance(): Promise<void> { // applies the requested statistics and final-boss identity without replacing other card details.
  const db: D1Database = database(); // keeps the update within one configured database.
  if (await db.prepare("SELECT id FROM installed_card_sets WHERE id = ?").bind(balance_id).first()) return; // skips a balance update already completed successfully.
  const patches = source_cards.map((card) => ({ id: card.id, difficulty: card.difficulty, health: card.health, speed: card.speed, damage_1: card.moves[0].damage, damage_2: card.moves[1].damage, identity: card.species_id === "0400" ? { species_name: card.species_name, art_prompt: card.art_prompt } : {}, name_1: card.species_id === "0400" ? card.moves[0].name : null, name_2: card.species_id === "0400" ? card.moves[1].name : null })); // limits the patch to requested balance fields and the time-boss concept.
  await db.batch([ // commits the complete update and completion marker together.
    db.prepare("UPDATE cards SET payload = json_set(json_patch(cards.payload, json_extract(p.value, '$.identity')), '$.difficulty', json_extract(p.value, '$.difficulty'), '$.health', json_extract(p.value, '$.health'), '$.speed', json_extract(p.value, '$.speed'), '$.moves[0].mana_cost', 1, '$.moves[1].mana_cost', 2, '$.moves[0].damage', json_extract(p.value, '$.damage_1'), '$.moves[1].damage', json_extract(p.value, '$.damage_2'), '$.moves[0].name', COALESCE(json_extract(p.value, '$.name_1'), json_extract(cards.payload, '$.moves[0].name')), '$.moves[1].name', COALESCE(json_extract(p.value, '$.name_2'), json_extract(cards.payload, '$.moves[1].name'))), revision = revision + 1 FROM json_each(?) AS p WHERE cards.id = json_extract(p.value, '$.id') AND NOT EXISTS (SELECT 1 FROM installed_card_sets WHERE id = ?)").bind(JSON.stringify(patches), balance_id), // updates existing set members by stable identity while preserving artwork, framing, ordinary names, prompts and deleted records.
    db.prepare("INSERT INTO installed_card_sets (id, installed_at) VALUES (?, ?) ON CONFLICT(id) DO NOTHING").bind(balance_id, Date.now()), // records completion only after the whole collection update succeeds.
  ]);
}
