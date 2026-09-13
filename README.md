# location_map_tool — dense branching 100-location adventure map

Open `index.html` in a modern browser.

## Automatic location art

Location art is loaded automatically from PNG files in the **same folder as `index.html`**.

The filename must exactly match the location name, followed by `.png`.

Examples:

- `Crystal caves` → `Crystal caves.png`
- `Great river plain` → `Great river plain.png`
- `Miller's crown` → `Miller's crown.png`
- `High crown castle` → `High crown castle.png`

There is no manual art assignment step. When the map renders a location, it requests that PNG automatically. If the file is not present, the location displays `no_art`. Renaming a location immediately changes the filename the tool looks for.

On case-sensitive systems or web servers, capitalization must match the location name exactly. Spaces and apostrophes are valid and are handled automatically by the browser.

The legacy `art` property is still preserved in imported/exported JSON for compatibility, but rendering no longer depends on it.

## Map topology

- exactly 100 locations
- 6 starting villages, each with exactly 1 connection
- `Stillwater sanctum`, with exactly 1 connection
- 75 ordinary locations with exactly 3 connections
- 18 ordinary locations with exactly 2 connections
- 134 total links
- 35 independent graph cycles
- clustered branches, local loops, splits and later reconnections
- all added dense links stay within their local regional clusters

Hard layout/routing rules remain enabled:

- infinite pannable canvas
- 20 px grid-snapped tiles
- tiles cannot overlap
- links use orthogonal grid routing
- links cannot cross or share route segments
- links cannot pass through tiles

The embedded preset is also supplied as `location_map.json`.

## monster card editor

The complete [card_foundry source](card_foundry/README.md) is included in this repository. [Open the hosted editor](https://card-foundry-cambell.cambellsmith.chatgpt.site) with its existing owner access.

- 400 standalone monsters, numbered `0001`–`0400`; exactly 80 each of fire, water, nature, light and dark.
- 133 easy, 133 medium and 133 hard monsters with interchangeable combat stats within each group, plus chronourobor, the time-loop boss at species 0400.
- Empty artwork fields with a complete generation prompt on every card; no evolutions.
- Editable species details, health, speed and two moves with mana cost and damage.
- Durable saves, artwork uploads, crop controls, PNG/SVG export and portable JSON objects with prompts.

The card editor is a separate server-backed application; the location map still opens from the root `index.html`. See [local setup](card_foundry/README.md#local-setup) to run the editor. The authored data is in [standalone_400.json](card_foundry/data/standalone_400.json), and [portable card objects](card_foundry/data/card_objects.json) are ready for other programs.
