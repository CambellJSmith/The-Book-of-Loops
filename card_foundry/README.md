# card_foundry

An original monster trading-card editor with a graphite studio interface.

- Fire, Water, Nature, Light, and Dark types.
- Species ID, species name, artwork, Health, Speed, and exactly two moves with name, Mana cost, and damage.
- Move 2 must always cost more Mana and deal more damage than Move 1.
- Durable card collection, raster artwork uploads, crop positioning, and unsaved-change protection.
- PNG export at 1500 × 2100 pixels from the same SVG used for the preview.
- Unique species IDs and optimistic revision checks protect saved data.

## Gameplay contract

Card Foundry stores the combat values printed on the cards. The current battle rules are:

- Every monster starts each battle with `0 Mana`.
- At the start of each of its turns, that monster gains exactly `1 Mana`.
- Mana accumulates until spent and resets when the battle ends.
- A move can only be used if the monster can pay its printed Mana cost; using it spends that amount.
- Move 1 is the cheaper, weaker move. Move 2 is always strictly more expensive and strictly more damaging.
- The player chooses an affordable move.
- The enemy rolls a d6: `1–3` selects Move 1 and `4–6` selects Move 2. If that move is unaffordable, it uses the other move if affordable; if neither is affordable, it makes no attack and keeps its Mana.

The canonical executable version of these rules lives in the repository root at `scripts/gameplay_rules.py`. The PDF build validates both retained 400-monster datasets against the Move 1 / Move 2 ordering invariant.

## Project structure

`components/editor` contains separate collection, property form, card artwork, and workspace components. `hooks` owns editor actions. `lib/card_model.ts` validates the complete card record, including the requirement that Move 2 has both a higher Mana cost and higher damage than Move 1. `lib/card_balance.ts` owns internal encounter progression and canonical combat scaling. `lib/server` isolates the database and file storage. `app/api` exposes checked request boundaries. `db/schema.ts` and `drizzle` own the database schema and generated migrations.

Internal encounter-progression metadata remains part of the canonical implementation, but it is not exposed by the card editor UI, printable book, browser map UI, accessibility labels, or portable player JSON.

## Development

Use the declared pnpm version and retained lockfile. The original hosted studio remains owner-private. This source copy contains logical storage bindings without the original hosted project identity. Generate a new migration after a database schema change.

## Artwork and exports

Upload PNG, JPEG, or WebP images. Images are normalized in the browser while retaining their aspect ratio, then stored separately from card records. Save the card after changing its artwork or framing. The editable Cindrel example contains original generated artwork and is not inserted into the saved collection automatically.

Exports include the current draft. Required names, supported statistic ranges, and the Move 1 / Move 2 ordering rule are checked before save or export. Card dimensions are pixel dimensions, with no implied print bleed or embedded print-resolution setting.

## Portable exports

The export menu offers PNG images, SVG design objects, one-card JSON, and saved-collection JSON. Current-card formats use the visible draft. Collection JSON fetches every saved card at export time and does not include unsaved edits.

SVG preserves named groups for the card frame, artwork, species identifier, type badge, species name, base statistics, and each move. Text stays text; frame and icon geometry stay vector shapes. Artwork is an embedded raster image. WebP artwork is losslessly converted to PNG for compatibility with SVG importers. All formats retain the single top-right type badge.

JSON files use this contract:

- `format`: `card_foundry`.
- `schema_version`: `3`.
- `cards`: an array of card objects, even for a single-card export.
- Each exported card has `species_id`, `species_name`, `type`, `is_final_boss`, `health`, `speed`, `moves`, `art`, and `art_prompt`.
- Implementation-only progression metadata is excluded from portable exports.
- `is_final_boss` is normally `false`; canonical species `0400` is the single `true` record.
- `moves` contains exactly two objects with `name`, `mana_cost`, and `damage`. Numeric fields remain JSON numbers.
- `art_prompt` is the editable, self-contained artwork generation brief. It is empty for cards without a brief and is not printed on the card.
- `art` is `null` for no artwork, or an object with `asset_id`, original pixel `width` and `height`, `zoom`, `position_x`, and `position_y`.
- Framing positions are percentages of the scaled image overflow. To recreate the current art window, scale the source image to cover a 694 × 610 rectangle, then multiply that scale by `zoom`. The displayed image starts at `(28 - overflow_x * position_x / 100, 28 - overflow_y * position_y / 100)` in the 750 × 1050 card viewBox and is clipped to the frame.
- `assets` maps each `asset_id` to `{ mime_type, encoding, data }`. The encoding is `base64`; `data` contains the base64 bytes without a data-URL prefix. Images shared by cards appear once in this map.

Load the complete JSON document with the target language's JSON parser. Card data is available through `cards`; decode the referenced asset with a base64 decoder, or combine its MIME type and base64 data into an image data URL. Exports contain no private artwork routes or internal database revisions. Importing the JSON back into this editor is not implemented.

## Standalone collection

The authored set contains exactly 400 unique species numbered `0001` through `0400`, interleaving 80 cards of each type. Every card has two unique move names and an empty artwork reference. Each saved `art_prompt` includes the complete shared watercolor style and a species-specific subject brief. Open `art_prompt` under artwork to edit or copy it; the prompt is included in both JSON exports. No evolution or family fields are used.

The canonical normal move profiles are:

| internal combat profile | Move 1 | Move 2 |
| --- | ---: | ---: |
| profile 1 | 1 Mana / 20 damage | 2 Mana / 40 damage |
| profile 2 | 1 Mana / 30 damage | 3 Mana / 70 damage |
| profile 3 | 2 Mana / 55 damage | 3 Mana / 90 damage |
| profile 4 | 2 Mana / 70 damage | 4 Mana / 125 damage |
| profile 5 | 3 Mana / 100 damage | 5 Mana / 180 damage |

These profiles are implementation data rather than player-facing classifications. In every profile, Move 2 is deliberately slower to unlock under the one-Mana-per-turn system and deals more damage when it becomes available.

Species `0400`, Duskervet, is the sole final boss. Its canonical attacks are `voidwhisker rend` at 4 Mana / 180 damage and `last eclipse` at 7 Mana / 360 damage, preserving the same stronger-second-move rule.

## Collection installation and canonical balance

The editor calls the idempotent `POST /api/card_sets/standalone_400` before loading its collection. Fresh databases install the canonical records directly. Existing databases use retained content-migration logic to bring surviving canonical records forward without restoring user-deleted cards or replacing uploaded artwork.

Canonical updates preserve uploaded artwork, crop/framing values, species names, unrelated editable fields, and user-deleted cards where the migration logic specifies. Card revisions are incremented where required so stale open editors cannot overwrite newer records.

Authored concepts live in `data/card_sets`; `scripts/build_card_set.py` validates and regenerates `data/standalone_400.json` reproducibly. The server applies the same canonical balancer to the bundled seed in memory when needed. The illustrated Cindrel starting-point button is an unsaved example, separate from the 400 blank-art collection records.

## Local setup

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

`data/card_objects.json` is the retained portable source snapshot used by the printable book. `data/standalone_400.json` is the reproducible canonical generator target. New player-facing JSON exports use portable schema version 3 and exclude implementation-only progression metadata. Attach generated artwork through the editor and save each card; the initial dataset deliberately leaves every artwork field empty.
