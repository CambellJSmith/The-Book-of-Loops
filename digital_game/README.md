# Digital Player

`digital_game` is a separate browser-based implementation of **The Book of Loops**. It reads the repository's canonical `location_map.json`, `card_foundry/data/card_objects.json`, and `healing_locations.json`, so map, encounter, monster-stat, and healing changes automatically flow into the playable version.

## Run it

From the repository root:

```bash
python digital_game/play.py
```

The launcher starts a local web server and opens the player in the default browser. It uses only the Python standard library. To start the server without opening a browser, use `python digital_game/play.py --no-browser`.

Opening `digital_game/index.html` directly from disk is not supported because browsers block the JSON data requests used by the player.

## Implemented gameplay

The digital player handles the full loop: random starting village and starter rolls, travel over the real map links, d6 encounters, Speed ordering and tie rolls, per-turn Mana gain, player move choice, enemy move rolls and affordability fallback, permanent monster death, recruitment rolls, the six-monster carry limit with immediate discard choice, all 25 healing locations, the final Duskervet encounter, game-over and victory states.

The app autosaves to browser `localStorage`. Saves can also be exported as JSON and imported later. There is no digital reserve or storage system; exported saves reject teams larger than six.

### Battle handling

Before each encounter the player chooses which carried monster enters battle. The printed rules do not define voluntary mid-battle switching, so the digital player does not add it. If the active monster dies and other carried monsters remain, the player chooses a replacement and the same enemy keeps its current Health and Mana.

A healing location can heal one damaged carried monster during that visit, before or after its encounter. Travelling away and returning creates a new visit.

## Files

- `index.html` — application shell
- `styles.css` — Blender-inspired dark interface
- `app.js` — browser UI, save system and game flow
- `engine.js` — reusable rules and battle functions
- `play.py` — dependency-free local launcher
- `tests/` — Node tests for the rules engine and repository data integration
