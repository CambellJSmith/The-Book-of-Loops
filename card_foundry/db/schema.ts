import { index, integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core"; // defines the durable card collection.

export const cards = sqliteTable("cards", { // stores validated card payloads with searchable identifiers.
  id: text("id").primaryKey(), // identifies each saved card.
  species_id: text("species_id").notNull(), // preserves custom species numbering.
  payload: text("payload").notNull(), // retains the complete validated monster data.
  revision: integer("revision").notNull().default(1), // protects newer edits from stale writes.
  created_at: integer("created_at").notNull(), // records initial creation time.
  updated_at: integer("updated_at").notNull(), // orders recently edited cards.
}, (table) => [uniqueIndex("idx_cards_species_id").on(table.species_id), index("idx_cards_updated_at").on(table.updated_at)]); // supports unique species and recent-card ordering.

export const installed_card_sets = sqliteTable("installed_card_sets", { // records completed collection imports independently of editable cards.
  id: text("id").primaryKey(), // prevents reimporting a set after cards are edited or deleted.
  installed_at: integer("installed_at").notNull(), // records when the complete set was installed.
});
