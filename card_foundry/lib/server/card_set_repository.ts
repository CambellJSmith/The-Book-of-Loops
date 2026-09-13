import source_cards from "@/data/standalone_400.json"; // bundles the authored collection only into the server import path.
import { balance_standalone_cards, difficulty_counts, element_difficulty_count } from "@/lib/card_balance"; // classifies concepts and applies the five-stage combat progression.
import { card_schema, difficulties, elements, type Difficulty, type Element, type MonsterCard } from "@/lib/card_model"; // checks every imported card against the normal save contract.
import { database } from "./storage"; // keeps durable storage access behind the existing boundary.

const legacy_set_id: string = "standalone_400_v1"; // identifies the original one-time collection installation.
const balance_set_id: string = "standalone_400_v2_difficulty"; // identifies the one-time difficulty rebalance for existing collections.
function validated_balanced_cards(): MonsterCard[] { // prepares one canonical balanced collection for both new installs and migrations.
  const source: MonsterCard[] = source_cards.map((card: unknown) => card_schema.parse(card)); // upgrades historical seed payloads with schema defaults before balancing.
  const cards: MonsterCard[] = balance_standalone_cards(source); // assigns content-aware difficulty and tier-scaled combat values.
  const counts: Record<Difficulty, number> = difficulty_counts(cards); // verifies the global eighty-card band targets.
  const boss: MonsterCard | undefined = cards.find((card: MonsterCard) => card.is_final_boss); // locates the unique climactic monster.
  if (cards.length !== 400 || elements.some((element: Element) => cards.filter((card: MonsterCard) => card.type === element).length !== 80) || new Set(cards.map((card: MonsterCard) => card.species_name)).size !== 400) throw new Error("the standalone collection is incomplete"); // prevents an incomplete or uneven installation.
  if (difficulties.some((difficulty: Difficulty) => counts[difficulty] !== 80) || elements.some((element: Element) => difficulties.some((difficulty: Difficulty) => element_difficulty_count(cards, element, difficulty) !== 16))) throw new Error("the standalone difficulty distribution is uneven"); // guarantees every band contains sixteen cards of every element.
  if (!boss || boss.species_id !== "0400" || cards.filter((card: MonsterCard) => card.is_final_boss).length !== 1 || boss.difficulty !== "ultra") throw new Error("the final boss assignment is invalid"); // guarantees card four hundred is the sole final boss and remains inside Ultra.
  return cards; // returns the checked collection only after all progression invariants pass.
}
export async function install_standalone_cards(): Promise<void> { // installs or rebalances the canonical set without restoring user-deleted cards.
  const db: D1Database = database(); // shares one database binding throughout the operation.
  const balance_installed = await db.prepare("SELECT id FROM installed_card_sets WHERE id = ?").bind(balance_set_id).first<{ id: string }>(); // avoids repeating the v2 rebalance after the user resumes editing.
  if (balance_installed) return; // keeps post-rebalance user edits authoritative on later visits.
  const cards: MonsterCard[] = validated_balanced_cards(); // prepares the same deterministic progression for every environment.
  const legacy_installed = await db.prepare("SELECT id FROM installed_card_sets WHERE id = ?").bind(legacy_set_id).first<{ id: string }>(); // distinguishes a fresh database from an existing v1 collection.
  const time: number = Date.now(); // establishes one consistent migration timestamp.
  if (!legacy_installed) { // installs balanced records directly when the original collection has never existed.
    await db.batch([ // commits the complete balanced seed and both completion markers together.
      db.prepare("INSERT INTO cards (id, species_id, payload, revision, created_at, updated_at) SELECT json_extract(value, '$.id'), json_extract(value, '$.species_id'), value, 1, ?, ? - CAST(json_extract(value, '$.species_id') AS INTEGER) FROM json_each(?) WHERE NOT EXISTS (SELECT 1 FROM installed_card_sets WHERE id = ?)").bind(time, time, JSON.stringify(cards), legacy_set_id), // preserves the established deterministic initial card ordering.
      db.prepare("INSERT INTO installed_card_sets (id, installed_at) VALUES (?, ?) ON CONFLICT(id) DO NOTHING").bind(legacy_set_id, time), // records compatibility with the original installer contract.
      db.prepare("INSERT INTO installed_card_sets (id, installed_at) VALUES (?, ?) ON CONFLICT(id) DO NOTHING").bind(balance_set_id, time), // records that the installed cards already contain the v2 progression.
    ]);
    return; // avoids running the existing-collection migration against the newly inserted cards.
  }
  const patches = cards.map((card: MonsterCard) => ({ id: card.id, core: { difficulty: card.difficulty, is_final_boss: card.is_final_boss, health: card.health, speed: card.speed, ...(card.is_final_boss ? { art_prompt: card.art_prompt, moves: card.moves } : {}) }, first_mana: card.moves[0].mana_cost, first_damage: card.moves[0].damage, second_mana: card.moves[1].mana_cost, second_damage: card.moves[1].damage })); // separates progression fields from numeric move updates so normal custom move names survive.
  const patch_json: string = JSON.stringify(patches); // keeps the four hundred small updates inside one bounded JSON parameter.
  await db.batch([ // applies the canonical rebalance and its completion marker atomically.
    db.prepare("UPDATE cards SET payload = (SELECT json_set(json_patch(cards.payload, json_extract(patch.value, '$.core')), '$.moves[0].mana_cost', json_extract(patch.value, '$.first_mana'), '$.moves[0].damage', json_extract(patch.value, '$.first_damage'), '$.moves[1].mana_cost', json_extract(patch.value, '$.second_mana'), '$.moves[1].damage', json_extract(patch.value, '$.second_damage')) FROM json_each(?) AS patch WHERE json_extract(patch.value, '$.id') = cards.id), revision = revision + 1 WHERE id IN (SELECT json_extract(value, '$.id') FROM json_each(?))").bind(patch_json, patch_json), // preserves normal move names and artwork while updating only canonical progression values; the boss core intentionally replaces its move names and art prompt.
    db.prepare("INSERT INTO installed_card_sets (id, installed_at) VALUES (?, ?) ON CONFLICT(id) DO NOTHING").bind(balance_set_id, time), // prevents the progression migration from overwriting later user edits.
  ]);
}
