from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"
CONFIG_PATH = ROOT / "healing_locations.json"

_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
HEALING_LOCATION_IDS = frozenset(str(location_id) for location_id in _config.get("location_ids", []))
HEALING_NOTE = str(_config.get("note", "")).strip()
if len(HEALING_LOCATION_IDS) != 25:
    raise RuntimeError(f"expected exactly 25 healing locations, found {len(HEALING_LOCATION_IDS)}")
if not HEALING_NOTE:
    raise RuntimeError("healing note cannot be empty")

HEALING_CSS = r'''

    /* healing location note */
    #healing_note {
        margin-top: 12px;
        padding: 10px 12px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
    }

    #healing_note[hidden] {
        display: none;
    }

    #healing_note .healing_note_text {
        margin-top: 5px;
        color: var(--text);
        font-size: 12px;
        line-height: 1.45;
    }
'''

HEALING_HTML = f'''

                    <section id="healing_note" hidden>
                        <label>healing</label>
                        <div class="healing_note_text">{HEALING_NOTE}</div>
                    </section>
'''


def healing_javascript() -> str:
    ids = ", ".join(f'"{location_id}"' for location_id in sorted(HEALING_LOCATION_IDS))
    return f'''
    const HEALING_LOCATION_IDS = new Set([{ids}]);

    function renderHealingNote(location) {{
        healingNote.hidden = !HEALING_LOCATION_IDS.has(String(location.id));
    }}

'''


def patch_index_html(html: str) -> str:
    if "/* healing location note */" not in html:
        html = html.replace("\n</style>", HEALING_CSS + "\n</style>", 1)

    if 'id="healing_note"' not in html:
        anchor = '                    <div id="encounter_table"></div>\n'
        if anchor not in html:
            raise RuntimeError("could not find encounter table anchor for healing section")
        html = html.replace(anchor, anchor + HEALING_HTML, 1)

    dom_anchor = '    const encounterTable = document.getElementById("encounter_table");\n'
    if 'document.getElementById("healing_note")' not in html:
        if dom_anchor not in html:
            raise RuntimeError("could not find encounter table DOM anchor for healing section")
        html = html.replace(
            dom_anchor,
            dom_anchor + '    const healingNote = document.getElementById("healing_note");\n',
            1,
        )

    if "function renderHealingNote(location)" not in html:
        update_anchor = "    function updateEditor() {\n"
        if update_anchor not in html:
            raise RuntimeError("could not find editor update anchor for healing section")
        html = html.replace(update_anchor, healing_javascript() + update_anchor, 1)

    render_anchor = "        renderEncounterTable(location);\n"
    if "        renderHealingNote(location);\n" not in html:
        if render_anchor not in html:
            raise RuntimeError("could not find encounter rendering anchor for healing section")
        html = html.replace(render_anchor, render_anchor + "        renderHealingNote(location);\n", 1)

    return html


def apply_index_patch() -> bool:
    current = INDEX_PATH.read_text(encoding="utf-8")
    updated = patch_index_html(current)
    if updated == current:
        return False
    INDEX_PATH.write_text(updated, encoding="utf-8")
    return True


def validate_index() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    if patch_index_html(html) != html:
        raise RuntimeError("index.html is missing the canonical healing-location patch")
    if html.count(HEALING_NOTE) != 1:
        raise RuntimeError("healing note must appear exactly once in the map tool template")
    missing_ids = [location_id for location_id in HEALING_LOCATION_IDS if f'"{location_id}"' not in html]
    if missing_ids:
        raise RuntimeError(f"map tool is missing healing location ids: {missing_ids}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply or validate the healing-location UI in index.html.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate_index()
        print(f"validated_healing_locations={len(HEALING_LOCATION_IDS)}")
        return
    changed = apply_index_patch()
    validate_index()
    print(f"healing_locations={len(HEALING_LOCATION_IDS)} index_updated={changed}")


if __name__ == "__main__":
    main()
