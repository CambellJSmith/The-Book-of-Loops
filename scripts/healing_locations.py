from __future__ import annotations

from collections import deque
from pathlib import Path
import json
import re

import gameplay_rules as game

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "location_map.json"
INDEX_PATH = ROOT / "index.html"
START_IDS = {f"loc_{index:03d}" for index in range(1, 7)}
BOSS_ID = "loc_100"


def adjacency_for(map_data: dict) -> dict[str, set[str]]:
    adjacency = {str(location["id"]): set() for location in map_data["locations"]}
    for link in map_data["links"]:
        source = str(link["source"])
        target = str(link["target"])
        if source in adjacency and target in adjacency:
            adjacency[source].add(target)
            adjacency[target].add(source)
    return adjacency


def graph_distances(adjacency: dict[str, set[str]], start: str) -> dict[str, int]:
    distances = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency.get(current, set()):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def select_healing_locations(map_data: dict) -> list[str]:
    adjacency = adjacency_for(map_data)
    ordered_ids = [str(location["id"]) for location in map_data["locations"]]
    eligible = [location_id for location_id in ordered_ids if location_id not in START_IDS and location_id != BOSS_ID]
    if len(eligible) < game.HEALING_LOCATION_COUNT:
        raise RuntimeError("not enough ordinary locations for the healing-location allocation")
    all_distances = {location_id: graph_distances(adjacency, location_id) for location_id in ordered_ids}
    order_index = {location_id: index for index, location_id in enumerate(ordered_ids)}
    start_distance = {
        location_id: min(all_distances[location_id].get(start_id, 10_000) for start_id in START_IDS)
        for location_id in eligible
    }
    selected: list[str] = []
    seed = max(eligible, key=lambda location_id: (start_distance[location_id], -order_index[location_id]))
    selected.append(seed)
    while len(selected) < game.HEALING_LOCATION_COUNT:
        remaining = [location_id for location_id in eligible if location_id not in selected]
        next_location = max(
            remaining,
            key=lambda location_id: (
                min(all_distances[location_id].get(chosen, 10_000) for chosen in selected),
                start_distance[location_id],
                -order_index[location_id],
            ),
        )
        selected.append(next_location)
    return selected


def apply_healing_flags(map_data: dict) -> list[str]:
    selected = set(select_healing_locations(map_data))
    for location in map_data["locations"]:
        location["healing_location"] = str(location["id"]) in selected
    map_data["healing_system"] = {
        "schema_version": 1,
        "location_count": game.HEALING_LOCATION_COUNT,
        "effect": game.HEALING_NOTE,
        "starting_villages_excluded": True,
        "stillwater_sanctum_excluded": True,
    }
    healing_ids = [str(location["id"]) for location in map_data["locations"] if location.get("healing_location")]
    if len(healing_ids) != game.HEALING_LOCATION_COUNT:
        raise RuntimeError(f"expected {game.HEALING_LOCATION_COUNT} healing locations, found {len(healing_ids)}")
    if set(healing_ids) & START_IDS or BOSS_ID in healing_ids:
        raise RuntimeError("healing locations must not include a starting village or Stillwater sanctum")
    return healing_ids


HEALING_CSS = r'''

    /* optional location healing action */
    .healing_note {
        margin-top: 9px;
        padding: 8px 9px;
        border: 1px solid #6f8f72;
        border-left: 3px solid #91c974;
        border-radius: 5px;
        background: #1f2922;
        color: #dce9dc;
        font-size: 10px;
        line-height: 1.45;
    }

    .healing_note strong {
        display: block;
        margin-bottom: 2px;
        color: #a9d68f;
        font-size: 10px;
        text-transform: lowercase;
    }
'''

HEALING_HTML = f'''
                    <div id="healing_note" class="healing_note" hidden>
                        <strong>healing</strong>
                        <span>{game.HEALING_NOTE}</span>
                    </div>
'''

HEALING_RENDER_HELPER = r'''
    function renderHealingNote(location) {
        healingNote.hidden = !Boolean(location.healing_location);
    }

'''


def patch_index(html: str, map_data: dict) -> str:
    preset = {"locations": map_data["locations"], "links": map_data["links"]}
    preset_text = json.dumps(preset, ensure_ascii=False, separators=(",", ":"))
    html, replacements = re.subn(
        r"    const PRESET_MAP = \{.*?\};\n\n    let data =",
        f"    const PRESET_MAP = {preset_text};\n\n    let data =",
        html,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise RuntimeError("could not replace PRESET_MAP while applying healing locations")

    if "/* optional location healing action */" not in html:
        html = html.replace("\n</style>", HEALING_CSS + "\n</style>", 1)
    if 'id="healing_note"' not in html:
        anchor = '                    <div id="encounter_table"></div>\n'
        if anchor not in html:
            raise RuntimeError("could not find encounter table for healing UI")
        html = html.replace(anchor, anchor + HEALING_HTML, 1)
    if 'document.getElementById("healing_note")' not in html:
        anchor = '    const encounterTable = document.getElementById("encounter_table");\n'
        if anchor not in html:
            raise RuntimeError("could not find encounter table DOM binding")
        html = html.replace(anchor, anchor + '    const healingNote = document.getElementById("healing_note");\n', 1)

    normalize_section = html.split("function normalizeLocation", 1)[1].split("function migrateParsedData", 1)[0]
    if "healing_location:" not in normalize_section:
        anchor = '            encounter_type_bias: normalizeEncounterBias(encounterSource.encounter_type_bias),\n'
        if anchor not in html:
            raise RuntimeError("could not find normalized encounter fields")
        html = html.replace(
            anchor,
            anchor + '            healing_location: Boolean(location.healing_location ?? presetLocation?.healing_location ?? false),\n',
            1,
        )
    if "function renderHealingNote(location)" not in html:
        html = html.replace("    function updateEditor() {\n", HEALING_RENDER_HELPER + "    function updateEditor() {\n", 1)
    if "        renderHealingNote(location);\n" not in html:
        anchor = "        renderEncounterTable(location);\n"
        if anchor not in html:
            raise RuntimeError("could not find encounter rendering call")
        html = html.replace(anchor, anchor + "        renderHealingNote(location);\n", 1)

    old_detail = '            detail.textContent = `${encounter.type} · ${encounterDifficultyLabel(encounter.difficulty)}${encounter.is_final_boss ? " · final boss" : ""}`;'
    new_detail = '            detail.textContent = `${encounter.type}${encounter.is_final_boss ? " · final boss" : ""}`;'
    html = html.replace(old_detail, new_detail)
    if "encounterDifficultyLabel(encounter.difficulty)" in html:
        raise RuntimeError("generated map UI would expose internal monster difficulty")

    help_anchor = "                    Roll a six-sided die at a location and use the matching monster in its <b>monster_encounters</b> table."
    healing_help = f" Healing locations are marked in the editor and let you choose one monster to restore to full Health."
    if help_anchor in html and healing_help.strip() not in html:
        html = html.replace(help_anchor, help_anchor + healing_help, 1)
    return html


def main() -> None:
    map_data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(map_data.get("locations"), list) or not isinstance(map_data.get("links"), list):
        raise RuntimeError("location_map.json does not contain locations and links")
    healing_ids = apply_healing_flags(map_data)
    MAP_PATH.write_text(json.dumps(map_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(patch_index(INDEX_PATH.read_text(encoding="utf-8"), map_data), encoding="utf-8")
    location_by_id = {str(location["id"]): str(location.get("name", location["id"])) for location in map_data["locations"]}
    print(f"healing_locations={len(healing_ids)}")
    print("healing_location_names=" + " | ".join(location_by_id[location_id] for location_id in healing_ids))


if __name__ == "__main__":
    main()
