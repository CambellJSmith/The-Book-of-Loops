# card_foundry

An original monster trading-card editor with a graphite studio interface.

- Fire, Water, Nature, Light, and Dark types.
- Easy, Medium, Hard, Extra Hard, and Ultra encounter difficulties.
- Species ID, species name, difficulty, artwork, health, speed, and exactly two moves with name, mana cost, and damage.
- Durable card collection, raster artwork uploads, crop positioning, and unsaved-change protection.
- PNG export at 1500 × 2100 pixels from the same SVG used for the preview.
- Unique species IDs and optimistic revision checks protect saved data.

## Project structure

`components/editor` contains separate collection, property form, card artwork, and workspace components. `hooks` owns editor actions. `lib/card_model.ts` validates the complete card record. `lib/card_balance.ts` owns concept-aware difficulty classification and canonical combat scaling. `lib/server` isolates the database and file storage. `app/api` exposes checked request boundaries. `db/schema.ts` and `drizzle` own the database schema and generated migrations.

## Development

Use the declared pnpm version and retained lockfile. The original hosted studio remains owner-private. This source copy contains logical storage bindings without the original hosted project identity. Generate a new migration after a database schema change. Difficulty does not require a database-column migration because complete card data is stored inside the existing validated JSON payload.

## Artwork and exports

Upload PNG, JPEG, or WebP images. Images are normalized in the browser while retaining their aspect ratio, then stored separately from card records. Save the card after changing its artwork or framing. The editable Cindrel example contains original generated artwork and is not inserted into the saved collection automatically.

Exports include the current draft. Required names and supported statistic ranges are checked before save or export. Card dimensions are pixel dimensions, with no implied print bleed or embedded print-resolution setting.

## Portable exports

The export menu offers PNG images, SVG design objects, one-card JSON, and saved-collection JSON. Current-card formats use the visible draft. Collection JSON fetches every saved card at export time and does not include unsaved edits.

SVG preserves named groups for the card frame, artwork, species identifier, type badge, species name, base statistics, and each move. Text stays text; frame and icon geometry stay vector shapes. Artwork is an embedded raster image. WebP artwork is losslessly converted to PNG for compatibility with SVG importers. All formats retain the single top-right type badge.

JSON files use this contract:

- `format`: `card_foundry`.
- `schema_version`: `2` for difficulty-aware exports.
- `cards`: an array of card objects, even for a single-card export.
- Each card has `species_id` (string, preserving leading zeros), `species_name`, `type`, `difficulty`, `is_final_boss`, `health`, `speed`, `moves`, `art`, and `art_prompt`.
- `difficulty` is one of `easy`, `medium`, `hard`, `extra_hard`, or `ultra`.
- `is_final_boss` is normally `false`; canonical species `0400` is the single `true` record.
- `moves` contains exactly two objects with `name`, `mana_cost`, and `damage`. Numeric fields remain JSON numbers.
- `art_prompt` is the editable, self-contained artwork generation brief. It is empty for cards without a brief and is not printed on the card.
- `art` is `null` for no artwork, or an object with `asset_id`, original pixel `width` and `height`, `zoom`, `position_x`, and `position_y`.
- Framing positions are percentages of the scaled image overflow. To recreate the current art window, scale the source image to cover a 694 × 610 rectangle, then multiply that scale by `zoom`. The displayed image starts at `(28 - overflow_x * position_x / 100, 28 - overflow_y * position_y / 100)` in the 750 × 1050 card viewBox and is clipped to the frame.
- `assets` maps each `asset_id` to `{ mime_type, encoding, data }`. The encoding is `base64`; `data` contains the base64 bytes without a data-URL prefix. Images shared by cards appear once in this map.

Load the complete JSON document with the target language's JSON parser. Card data is available through `cards`; decode the referenced asset with a base64 decoder, or combine its MIME type and base64 data into an image data URL. Exports contain no private artwork routes or internal database revisions. Importing the JSON back into this editor is not implemented.

## Standalone collection

The authored set contains exactly 400 unique species numbered `0001` through `0400`, interleaving 80 cards of each type. Every card has two unique move names and an empty artwork reference. Each saved `art_prompt` includes the complete shared watercolor style and a species-specific subject brief. Open `art_prompt` under artwork to edit or copy it; the prompt is included in both JSON exports. No evolution or family fields are used.

The 400 monsters are divided into five content-aware encounter bands: Easy, Medium, Hard, Extra Hard, and Ultra. Each band contains exactly 80 monsters, with exactly 16 Fire, 16 Water, 16 Nature, 16 Light, and 16 Dark monsters. Classification is performed independently inside each element by scoring the authored creature description and move language for threat cues such as physical scale, armour, dangerous creature archetypes, magical intensity, destructive attacks, and deliberately gentle or diminutive traits. Species number is only a stable tiebreaker and does not determine normal difficulty.

Normal difficulty scaling preserves each monster's original durability-versus-speed identity while increasing its total combat budget:

| difficulty | health + speed | move 1 | move 2 |
| --- | ---: | ---: | ---: |
| Easy | 150 | 1 mana / 20 damage | 2 mana / 40 damage |
| Medium | 190 | 1 mana / 30 damage | 3 mana / 70 damage |
| Hard | 235 | 2 mana / 55 damage | 3 mana / 90 damage |
| Extra Hard | 285 | 2 mana / 70 damage | 4 mana / 125 damage |
| Ultra | 340 | 3 mana / 100 damage | 5 mana / 180 damage |

Species `0400`, Duskervet, is the sole final boss. It remains in the Ultra group but deliberately exceeds the normal Ultra envelope at 540 health and 160 speed. Its canonical attacks are `voidwhisker rend` at 4 mana / 180 damage and `last eclipse` at 7 mana / 360 damage. Its generated artwork prompt replaces the original compact Duskervet presentation with a colossal nine-tailed eclipse sovereign designed to read as the climactic opponent.

The editor groups the saved collection by difficulty and exposes difficulty as an editable card property. The final-boss role is stored separately through `is_final_boss`, so Ultra can still contain ordinary endgame monsters.

## Collection installation and rebalance

The editor calls the idempotent `POST /api/card_sets/standalone_400` before loading its collection. Fresh databases install the difficulty-balanced records directly. Databases that already completed the original `standalone_400_v1` installation receive one `standalone_400_v2_difficulty` content migration.

The v2 migration updates difficulty, final-boss metadata, health, speed, and move balance only on surviving canonical card identities. Uploaded artwork, crop/framing values, species names, unrelated editable fields, and user-deleted cards are preserved. The final boss also receives its new canonical artwork prompt. Card revisions are incremented so stale open editors cannot overwrite the rebalance. Once the v2 completion marker exists, later user edits remain authoritative and are not repeatedly rebalanced.

Authored concepts live in `data/card_sets`; `scripts/build_card_set.py` validates and regenerates `data/standalone_400.json` reproducibly with all five difficulty bands and the final-boss record materialized. The server also applies the same balancer to the bundled seed in memory, allowing existing v1 seed data to migrate safely. The illustrated Cindrel starting-point button is an unsaved Easy example, separate from the 400 blank-art collection records.

## local setup

The editor uses Node.js, pnpm, React/Vinext and Cloudflare D1/R2. It is not a static HTML page and cannot run directly on GitHub Pages. The root location-map tool remains independent.

With Node.js satisfying `package.json` and the declared pnpm version installed, run these commands from `card_foundry`:

```sh
pnpm install --frozen-lockfile
pnpm build
pnpm exec wrangler d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_hard_forge.sql
pnpm exec wrangler d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0001_late_leper_queen.sql
pnpm start
```

Apply the two SQL files only once to a fresh local database. They create the schema; the application installs the 400 cards when the editor first loads. Open the localhost URL printed by Wrangler. Local data and uploaded artwork stay under `.wrangler/state`, which is ignored by Git. Production hosting must provide D1/R2 bindings and apply the schema migrations; the repository contains no production credentials.

`data/card_objects.json` is the retained pre-difficulty portable snapshot. New exports from the editor use portable schema version 2 and include difficulty/final-boss metadata. `data/standalone_400.json` is the generator target; running `scripts/build_card_set.py` rematerializes it with the v2 progression fields. Attach generated artwork through the editor and save each card; the initial dataset deliberately leaves every artwork field empty.
