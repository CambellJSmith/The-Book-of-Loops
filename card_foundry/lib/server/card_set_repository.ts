import source_cards from "@/data/standalone_400.json"; // bundles the authored collection only into the server import path.
import { card_schema, elements, type MonsterCard } from "@/lib/card_model"; // checks every imported card against the normal save contract.
import { database } from "./storage"; // keeps durable storage access behind the existing boundary.

const set_id: string = "standalone_400_v1"; // identifies this one-time collection installation.
export async function install_standalone_cards(): Promise<void> { // installs the requested set atomically while preserving subsequent edits and deletions.
  const db: D1Database = database(); // shares one database binding throughout the operation.
  const installed = await db.prepare("SELECT id FROM installed_card_sets WHERE id = ?").bind(set_id).first<{ id: string }>(); // avoids reparsing the bundled set on later visits.
  if (installed) return; // keeps the user-owned collection authoritative after installation.
  const cards: MonsterCard[] = source_cards.map((card: unknown) => card_schema.parse(card)); // validates all imported fields before writing any rows.
  if (cards.length !== 400 || elements.some((element) => cards.filter((card: MonsterCard) => card.type === element).length !== 80) || new Set(cards.map((card: MonsterCard) => card.species_name)).size !== 400) throw new Error("the standalone collection is incomplete"); // prevents an incomplete or uneven installation.
  const time: number = Date.now(); // establishes a consistent installation timestamp.
  await db.batch([ // commits card insertion and its completion marker as one transaction.
    db.prepare("INSERT INTO cards (id, species_id, payload, revision, created_at, updated_at) SELECT json_extract(value, '$.id'), json_extract(value, '$.species_id'), value, 1, ?, ? - CAST(json_extract(value, '$.species_id') AS INTEGER) FROM json_each(?) WHERE NOT EXISTS (SELECT 1 FROM installed_card_sets WHERE id = ?)").bind(time, time, JSON.stringify(cards), set_id), // uses one bounded JSON parameter and preserves existing records through normal uniqueness constraints.
    db.prepare("INSERT INTO installed_card_sets (id, installed_at) VALUES (?, ?) ON CONFLICT(id) DO NOTHING").bind(set_id, time), // marks completion only when every card was inserted successfully.
  ]);
}
