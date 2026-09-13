import { card_schema, type MonsterCard } from "@/lib/card_model"; // validates records loaded from durable storage.
import { database } from "./storage"; // accesses the configured database.

interface CardRow { payload: string; revision: number; } // represents the persisted payload and revision.
function decode_card(row: CardRow): MonsterCard { // restores a validated card with its authoritative revision.
  return card_schema.parse({ ...JSON.parse(row.payload), revision: row.revision }); // rejects malformed stored records.
}
export async function read_cards(): Promise<MonsterCard[]> { // loads the saved card collection in recent-edit order.
  const result = await database().prepare("SELECT payload, revision FROM cards ORDER BY updated_at DESC, id DESC").all<CardRow>(); // uses the recent-card index without truncating the collection.
  return result.results.map(decode_card); // returns checked monster data.
}
export async function write_card(card: MonsterCard): Promise<MonsterCard | null> { // atomically saves a new card or updates an expected revision.
  const time: number = Date.now(); // records when this save occurred.
  let row: CardRow | null; // captures the successfully written record.
  if (card.revision === 0) { // creates an unsaved card without replacing an existing record.
    row = await database().prepare("INSERT INTO cards (id, species_id, payload, revision, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?) ON CONFLICT(id) DO NOTHING RETURNING payload, revision").bind(card.id, card.species_id, JSON.stringify(card), time, time).first<CardRow>(); // rejects collisions on an existing record identity.
  } else { // requires the saved revision to still match the editor.
    row = await database().prepare("UPDATE cards SET species_id = ?, payload = ?, revision = revision + 1, updated_at = ? WHERE id = ? AND revision = ? RETURNING payload, revision").bind(card.species_id, JSON.stringify(card), time, card.id, card.revision).first<CardRow>(); // protects concurrent edits with an atomic comparison.
  }
  return row ? decode_card(row) : null; // signals a conflict when no revision matched.
}
export async function delete_card(id: string, revision: number): Promise<boolean> { // removes only the version reviewed by the user.
  const row = await database().prepare("DELETE FROM cards WHERE id = ? AND revision = ? RETURNING id").bind(id, revision).first<{ id: string }>(); // prevents deleting an unseen newer edit.
  return Boolean(row); // reports whether a matching record was deleted.
}
