from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"
MAP_PATH = ROOT / "location_map.json"
MANIFEST_PATH = ROOT / "monster_encounters.json"
CONCEPT_DIR = ROOT / "card_foundry" / "data" / "card_sets"

TYPES = ("fire", "water", "nature", "light", "dark")
DIFFICULTIES = ("easy", "medium", "hard", "extra_hard", "ultra")
DIFFICULTY_INDEX = {difficulty: index for index, difficulty in enumerate(DIFFICULTIES)}
TARGET_PROGRESS = {"easy": 0.10, "medium": 0.31, "hard": 0.50, "extra_hard": 0.70, "ultra": 0.88}
START_IDS = {f"loc_{index:03d}" for index in range(1, 7)}
BOSS_ID = "loc_100"
FINAL_BOSS_SPECIES = "0400"

POSITIVE_TERMS = (
    ("colossal", 10), ("giant", 6), ("huge", 6), ("massive", 6), ("fortress", 5),
    ("ancient", 4), ("guardian", 4), ("golem", 4), ("dragon", 6), ("basilisk", 6),
    ("tyrant", 5), ("rhinoceros", 4), ("lion", 3), ("walrus", 3), ("crocodilian", 4),
    ("sharklike", 4), ("scorpion", 4), ("raptor", 3), ("buffalo", 4), ("bear", 3),
    ("armoured", 3), ("armored", 3), ("heavy", 3), ("muscular", 3), ("strong", 3),
    ("broad shouldered", 2), ("basalt", 2), ("obsidian", 2), ("iron", 1), ("molten", 2),
    ("lava", 4), ("storm", 3), ("abyss", 3), ("whirlpool", 3), ("geyser", 3),
    ("furnace", 3), ("solar", 2), ("oracle", 3), ("knight", 2), ("sabre toothed", 4),
    ("carnivorous", 4), ("hornet", 3), ("serpent", 2),
)
NEGATIVE_TERMS = (
    ("thimble sized", -7), ("tiny", -6), ("small", -4), ("little", -4), ("delicate", -3),
    ("gentle", -3), ("cheerful", -3), ("playful", -3), ("friendly", -3), ("soft", -2),
    ("plump", -1), ("round", -1), ("curious", -1), ("sprite", -2), ("compact", -1),
)
DANGEROUS_MOVE_TERMS = (
    ("crush", 4), ("eruption", 4), ("avalanche", 5), ("detonation", 5), ("inferno", 5),
    ("eclipse", 3), ("upheaval", 5), ("roar", 3), ("barrage", 4), ("charge", 2),
    ("torrent", 2), ("deluge", 4), ("quake", 4), ("blast", 4), ("cyclone", 4),
    ("stampede", 4), ("furnace", 4), ("blaze", 3), ("squall", 3), ("downpour", 3),
    ("gale", 2), ("ram", 2), ("pounce", 2), ("constrict", 3), ("sting", 2),
    ("slash", 2), ("beam", 2), ("surge", 1), ("rush", 1), ("wave", 1),
)
GENTLE_MOVE_TERMS = (
    ("tap", -2), ("flick", -2), ("glint", -2), ("nudge", -2), ("hop", -1),
    ("clink", -1), ("dab", -1), ("bop", -1), ("whisk", -1), ("skip", -1),
    ("flutter", -1), ("step", -1),
)

TYPE_TERMS = {
    "water": (
        ("river", 5), ("water", 5), ("brook", 6), ("ford", 6), ("tarn", 6), ("lake", 6),
        ("marsh", 7), ("fen", 7), ("bog", 7), ("wetland", 7), ("coast", 7), ("shore", 7),
        ("sea", 7), ("bay", 7), ("cove", 7), ("tide", 7), ("pool", 5), ("well", 6),
        ("spring", 7), ("flood", 6), ("waterfall", 7), ("cascade", 6), ("stream", 5),
        ("reed", 4), ("rain", 5), ("ice", 6), ("glacier", 7), ("snow", 4), ("aqueduct", 7),
        ("canal", 6), ("cistern", 6), ("sluice", 7), ("harbour", 7), ("wreck", 4),
    ),
    "nature": (
        ("wood", 6), ("forest", 7), ("grove", 7), ("orchard", 8), ("meadow", 8),
        ("prairie", 7), ("grass", 4), ("field", 6), ("farm", 7), ("flower", 6),
        ("garden", 8), ("root", 6), ("tree", 6), ("thorn", 6), ("clover", 7),
        ("moss", 6), ("fern", 7), ("pine", 6), ("willow", 7), ("beech", 7),
        ("pasture", 7), ("valley", 3), ("hollow", 4), ("vine", 6), ("fruit", 6),
        ("reed", 4), ("bog", 3), ("marsh", 3), ("garden", 8), ("bloom", 6),
    ),
    "fire": (
        ("smith", 8), ("forge", 9), ("furnace", 9), ("kiln", 9), ("copper", 6),
        ("iron", 5), ("industrial", 8), ("workshop", 5), ("mine", 6), ("mineral", 5),
        ("volcanic", 10), ("lava", 10), ("ash", 8), ("coal", 9), ("glass", 5),
        ("desert", 6), ("hot", 7), ("heat", 8), ("fire", 9), ("soot", 7),
        ("brick", 6), ("chimney", 7), ("engine", 7), ("brass", 5), ("metal", 4),
        ("lightning", 4), ("stormscar", 4),
    ),
    "light": (
        ("shrine", 8), ("chapel", 9), ("sanctum", 10), ("sun", 8), ("solar", 9),
        ("moon", 6), ("star", 8), ("sky", 6), ("crown", 7), ("summit", 6),
        ("bluff", 4), ("monument", 6), ("crystal", 7), ("white", 5), ("silver", 5),
        ("lighthouse", 9), ("beacon", 8), ("observatory", 10), ("celestial", 10),
        ("ceremonial", 7), ("sacred", 9), ("altar", 8), ("pilgrim", 8), ("temple", 9),
        ("marble", 5), ("radiant", 8), ("light", 6), ("aurora", 9), ("heavens", 9),
    ),
    "dark": (
        ("cave", 7), ("cavern", 8), ("crypt", 10), ("tomb", 10), ("burial", 9),
        ("underground", 8), ("tunnel", 6), ("sealed", 5), ("abandoned", 4), ("ruin", 5),
        ("dark", 8), ("black", 6), ("midnight", 10), ("dusk", 8), ("shadow", 8),
        ("chasm", 8), ("gorge", 5), ("mine", 5), ("grave", 10), ("ancient", 4),
        ("forgotten", 5), ("hidden", 4), ("buried", 7), ("vault", 8), ("depth", 7),
        ("faceless", 8), ("throne", 6), ("seal", 7), ("obsidian", 7), ("inner", 3),
    ),
}


def normalized_words(value: str) -> str:
    return f" {' '.join(''.join(character if character.isalnum() else ' ' for character in value.lower()).split())} "


def weighted_score(text: str, terms: tuple[tuple[str, int], ...]) -> int:
    haystack = normalized_words(text)
    return sum(weight for term, weight in terms if normalized_words(term) in haystack)


def stable_hash(value: str) -> int:
    result = 2166136261
    for byte in value.encode("utf-8"):
        result ^= byte
        result = (result * 16777619) & 0xFFFFFFFF
    return result


def load_monsters() -> list[dict]:
    rows_by_type: dict[str, list[list[str]]] = {}
    for element in TYPES:
        rows = [line.split("|") for line in (CONCEPT_DIR / f"{element}_concepts.tsv").read_text().splitlines() if line.strip()]
        if len(rows) != 80 or any(len(row) != 4 for row in rows):
            raise RuntimeError(f"invalid concept source for {element}")
        rows_by_type[element] = rows

    monsters: list[dict] = []
    for source_index in range(80):
        for element_index, element in enumerate(TYPES):
            name, subject, first_move, second_move = rows_by_type[element][source_index]
            species_id = str(source_index * len(TYPES) + element_index + 1).zfill(4)
            concept = f"{name} {subject}"
            moves = f"{first_move} {second_move}"
            threat = (
                weighted_score(concept, POSITIVE_TERMS)
                + weighted_score(concept, NEGATIVE_TERMS)
                + weighted_score(moves, DANGEROUS_MOVE_TERMS)
                + weighted_score(moves, GENTLE_MOVE_TERMS)
            )
            if species_id == FINAL_BOSS_SPECIES:
                threat = 1_000_000
            monsters.append({
                "species_id": species_id,
                "species_name": name,
                "type": element,
                "difficulty": "easy",
                "threat": threat,
                "is_final_boss": species_id == FINAL_BOSS_SPECIES,
            })

    for element in TYPES:
        ranked = sorted(
            (monster for monster in monsters if monster["type"] == element),
            key=lambda monster: (monster["threat"], monster["species_id"]),
        )
        if len(ranked) != 80:
            raise RuntimeError(f"expected 80 {element} monsters")
        for rank, monster in enumerate(ranked):
            monster["difficulty"] = DIFFICULTIES[min(4, rank // 16)]

    boss = next(monster for monster in monsters if monster["species_id"] == FINAL_BOSS_SPECIES)
    boss["difficulty"] = "ultra"
    if Counter(monster["difficulty"] for monster in monsters) != Counter({difficulty: 80 for difficulty in DIFFICULTIES}):
        raise RuntimeError("monster difficulty distribution no longer matches the card foundry")
    return monsters


def adjacency_for(map_data: dict) -> dict[str, set[str]]:
    adjacency = {str(location["id"]): set() for location in map_data["locations"]}
    for link in map_data["links"]:
        source = str(link["source"])
        target = str(link["target"])
        if source in adjacency and target in adjacency:
            adjacency[source].add(target)
            adjacency[target].add(source)
    return adjacency


def graph_distances(adjacency: dict[str, set[str]], starts: set[str]) -> dict[str, int]:
    distances: dict[str, int] = {}
    queue: deque[str] = deque()
    for start in starts:
        if start in adjacency:
            distances[start] = 0
            queue.append(start)
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def location_progress(map_data: dict) -> dict[str, float]:
    adjacency = adjacency_for(map_data)
    start_distance = graph_distances(adjacency, START_IDS)
    boss_distance = graph_distances(adjacency, {BOSS_ID})
    progress: dict[str, float] = {}
    for location in map_data["locations"]:
        location_id = str(location["id"])
        if location_id == BOSS_ID:
            progress[location_id] = 1.0
            continue
        from_start = start_distance.get(location_id)
        to_boss = boss_distance.get(location_id)
        if from_start is None or to_boss is None:
            progress[location_id] = 0.5
            continue
        denominator = from_start + to_boss
        progress[location_id] = 0.0 if denominator == 0 else from_start / denominator
    return progress


def type_bias(location: dict) -> dict[str, int]:
    text = normalized_words(f"{location.get('name', '')} {location.get('description', '')}")
    weights = {element: 1 for element in TYPES}
    for element, terms in TYPE_TERMS.items():
        for term, weight in terms:
            if normalized_words(term) in text:
                weights[element] += weight
    return weights


def unique_capacity(progress: float) -> int:
    return 3 + int(progress >= 0.25) + int(progress >= 0.50) + int(progress >= 0.75)


def allowed_difficulties(progress: float) -> set[str]:
    if progress < 0.12:
        return {"easy"}
    if progress < 0.28:
        return {"easy", "medium"}
    if progress < 0.45:
        return {"easy", "medium", "hard"}
    if progress < 0.62:
        return {"medium", "hard", "extra_hard"}
    if progress < 0.78:
        return {"hard", "extra_hard", "ultra"}
    if progress < 0.90:
        return {"extra_hard", "ultra"}
    return {"ultra"}


def monster_location_score(monster: dict, location: dict, progress: float, biases: dict[str, int], occupied: int = 0) -> float:
    progression_cost = abs(progress - TARGET_PROGRESS[monster["difficulty"]]) * 190.0
    type_reward = biases[monster["type"]] * 12.0
    occupancy_cost = occupied * 9.0
    tie_break = (stable_hash(f"{monster['species_id']}:{location['id']}") % 1000) / 1000.0
    return progression_cost - type_reward + occupancy_cost + tie_break


def choose_monster_for_location(
    available: list[dict], location: dict, progress: float, biases: dict[str, int], already: list[dict]
) -> dict:
    allowed = allowed_difficulties(progress)
    candidates = [monster for monster in available if monster["difficulty"] in allowed]
    if not candidates:
        candidates = available
    return min(
        candidates,
        key=lambda monster: monster_location_score(monster, location, progress, biases, len(already)),
    )


def choose_location_for_monster(
    monster: dict,
    locations: list[dict],
    progress: dict[str, float],
    biases: dict[str, dict[str, int]],
    assignments: dict[str, list[dict]],
    capacities: dict[str, int],
) -> dict:
    candidates = [
        location
        for location in locations
        if len(assignments[location["id"]]) < capacities[location["id"]]
        and monster["difficulty"] in allowed_difficulties(progress[location["id"]])
    ]
    if not candidates:
        candidates = [
            location
            for location in locations
            if len(assignments[location["id"]]) < capacities[location["id"]]
            and not (location["id"] in START_IDS and monster["difficulty"] != "easy")
        ]
    if not candidates:
        raise RuntimeError(f"no encounter capacity remains for #{monster['species_id']}")
    return min(
        candidates,
        key=lambda location: monster_location_score(
            monster,
            location,
            progress[location["id"]],
            biases[location["id"]],
            len(assignments[location["id"]]),
        ),
    )


def build_roll_table(location_id: str, monsters: list[dict], biases: dict[str, int]) -> list[dict]:
    if location_id == BOSS_ID:
        boss = monsters[0]
        return [encounter_record(roll, boss) for roll in range(1, 7)]
    if not monsters:
        return []
    repeat_order = sorted(
        monsters,
        key=lambda monster: (
            DIFFICULTY_INDEX[monster["difficulty"]],
            -biases[monster["type"]],
            monster["species_id"],
        ),
    )
    faces = list(monsters)
    repeat_index = 0
    while len(faces) < 6:
        faces.append(repeat_order[repeat_index % len(repeat_order)])
        repeat_index += 1
    indexed = list(enumerate(faces[:6]))
    indexed.sort(key=lambda item: stable_hash(f"{location_id}:{item[0]}:{item[1]['species_id']}"))
    return [encounter_record(roll, monster) for roll, (_, monster) in enumerate(indexed, start=1)]


def encounter_record(roll: int, monster: dict) -> dict:
    return {
        "roll": roll,
        "species_id": monster["species_id"],
        "species_name": monster["species_name"],
        "type": monster["type"],
        "difficulty": monster["difficulty"],
        "is_final_boss": bool(monster.get("is_final_boss", False)),
    }


def distribute_encounters(map_data: dict, monsters: list[dict]) -> dict:
    progress = location_progress(map_data)
    location_by_id = {str(location["id"]): location for location in map_data["locations"]}
    if BOSS_ID not in location_by_id or location_by_id[BOSS_ID].get("name") != "Stillwater sanctum":
        raise RuntimeError("Stillwater sanctum is not the expected final location")
    ordinary_locations = [location for location in map_data["locations"] if location["id"] != BOSS_ID]
    ordinary_locations.sort(key=lambda location: (progress[location["id"]], location["id"]))
    biases = {location["id"]: type_bias(location) for location in ordinary_locations}
    capacities = {location["id"]: unique_capacity(progress[location["id"]]) for location in ordinary_locations}
    if sum(capacities.values()) < 399:
        raise RuntimeError("location capacity is insufficient for all ordinary monsters")
    assignments: dict[str, list[dict]] = {location["id"]: [] for location in ordinary_locations}
    available = [monster for monster in monsters if monster["species_id"] != FINAL_BOSS_SPECIES]

    for location in ordinary_locations:
        for _ in range(3):
            chosen = choose_monster_for_location(
                available,
                location,
                progress[location["id"]],
                biases[location["id"]],
                assignments[location["id"]],
            )
            assignments[location["id"]].append(chosen)
            available.remove(chosen)

    remaining_order = sorted(
        available,
        key=lambda monster: (
            {"easy": 0, "ultra": 1, "medium": 2, "extra_hard": 3, "hard": 4}[monster["difficulty"]],
            monster["species_id"],
        ),
    )
    for monster in remaining_order:
        location = choose_location_for_monster(monster, ordinary_locations, progress, biases, assignments, capacities)
        assignments[location["id"]].append(monster)

    placed_ids = [monster["species_id"] for values in assignments.values() for monster in values]
    if len(placed_ids) != 399 or len(set(placed_ids)) != 399:
        raise RuntimeError("ordinary monsters were not placed exactly once")
    if any(len(values) < 3 or len(values) > 6 for values in assignments.values()):
        raise RuntimeError("ordinary location unique encounter count is outside 3..6")
    for start_id in START_IDS:
        if any(monster["difficulty"] != "easy" for monster in assignments[start_id]):
            raise RuntimeError(f"starting location {start_id} contains a non-easy monster")

    boss = next(monster for monster in monsters if monster["species_id"] == FINAL_BOSS_SPECIES)
    for location in map_data["locations"]:
        location_id = str(location["id"])
        if location_id == BOSS_ID:
            unique_monsters = [boss]
            location_bias = type_bias(location)
        else:
            unique_monsters = assignments[location_id]
            location_bias = biases[location_id]
        location["encounter_progress"] = round(progress[location_id], 3)
        location["encounter_type_bias"] = dict(sorted(location_bias.items(), key=lambda item: (-item[1], item[0])))
        location["encounters"] = build_roll_table(location_id, unique_monsters, location_bias)

    all_rolls = [entry for location in map_data["locations"] for entry in location["encounters"]]
    if any(len(location["encounters"]) != 6 for location in map_data["locations"]):
        raise RuntimeError("every location must have six d6 outcomes")
    if any(len({entry["species_id"] for entry in location["encounters"]}) > 6 for location in map_data["locations"]):
        raise RuntimeError("a location exceeds six unique monsters")
    boss_location = location_by_id[BOSS_ID]
    if {entry["species_id"] for entry in boss_location["encounters"]} != {FINAL_BOSS_SPECIES}:
        raise RuntimeError("Stillwater sanctum contains a non-boss encounter")
    if any(entry["species_id"] == FINAL_BOSS_SPECIES for location in ordinary_locations for entry in location["encounters"]):
        raise RuntimeError("final boss appears outside Stillwater sanctum")

    top_bias_matches = 0
    ordinary_placements = 0
    for location in ordinary_locations:
        highest = max(biases[location["id"]].values())
        preferred = {element for element, weight in biases[location["id"]].items() if weight == highest}
        for monster in assignments[location["id"]]:
            ordinary_placements += 1
            if monster["type"] in preferred or highest == 1:
                top_bias_matches += 1

    return {
        "assignments": assignments,
        "progress": progress,
        "biases": biases,
        "rolls": all_rolls,
        "top_bias_match_rate": round(top_bias_matches / max(1, ordinary_placements), 3),
    }


ENCOUNTER_CSS = r'''

    /* monster encounter table */
    #encounter_meta {
        margin-top: 7px;
        color: var(--muted);
        font-size: 10px;
        line-height: 1.4;
    }

    #encounter_table {
        margin-top: 7px;
        display: grid;
        gap: 4px;
    }

    .encounter_row {
        display: grid;
        grid-template-columns: 26px minmax(0, 1fr);
        gap: 7px;
        align-items: center;
        padding: 6px 7px;
        border: 1px solid #44474e;
        border-radius: 5px;
        background: #232428;
    }

    .encounter_die {
        display: grid;
        place-items: center;
        width: 24px;
        height: 24px;
        border: 1px solid #5a5e66;
        border-radius: 4px;
        background: #303238;
        color: #fff;
        font-size: 11px;
        font-weight: 700;
    }

    .encounter_monster {
        min-width: 0;
        display: grid;
        gap: 2px;
    }

    .encounter_monster strong {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 11px;
        font-weight: 650;
    }

    .encounter_monster small {
        color: var(--muted);
        font-size: 9px;
        text-transform: lowercase;
    }

    .encounter_row[data-type="fire"] { border-left: 3px solid #f29255; }
    .encounter_row[data-type="water"] { border-left: 3px solid #60bff5; }
    .encounter_row[data-type="nature"] { border-left: 3px solid #91c974; }
    .encounter_row[data-type="light"] { border-left: 3px solid #ead58a; }
    .encounter_row[data-type="dark"] { border-left: 3px solid #b49bea; }
    .encounter_row.final_boss { border-color: #b49bea; box-shadow: inset 0 0 0 1px #b49bea55; }
'''

ENCOUNTER_HTML = r'''

                    <label>monster_encounters · roll_d6</label>
                    <div id="encounter_meta"></div>
                    <div id="encounter_table"></div>
'''

NORMALIZE_HELPERS = r'''
    function normalizeEncounters(encounters) {
        if (!Array.isArray(encounters)) return [];
        const validTypes = new Set(["fire", "water", "nature", "light", "dark"]);
        const validDifficulties = new Set(["easy", "medium", "hard", "extra_hard", "ultra"]);
        return encounters.slice(0, 6).map((entry, index) => ({
            roll: index + 1,
            species_id: String(entry?.species_id || "").padStart(4, "0"),
            species_name: String(entry?.species_name || "unknown_monster"),
            type: validTypes.has(entry?.type) ? entry.type : "dark",
            difficulty: validDifficulties.has(entry?.difficulty) ? entry.difficulty : "easy",
            is_final_boss: Boolean(entry?.is_final_boss)
        }));
    }

    function normalizeEncounterBias(value) {
        const result = {};
        for (const type of ["fire", "water", "nature", "light", "dark"]) {
            result[type] = Number.isFinite(value?.[type]) ? Math.max(0, Math.trunc(value[type])) : 1;
        }
        return result;
    }

'''

RENDER_HELPER = r'''
    function encounterDifficultyLabel(value) {
        return value === "extra_hard" ? "extra hard" : value;
    }

    function renderEncounterTable(location) {
        encounterTable.replaceChildren();
        const encounters = Array.isArray(location.encounters) ? location.encounters : [];
        if (encounters.length === 0) {
            encounterMeta.textContent = "no encounter table assigned";
            return;
        }
        const uniqueCount = new Set(encounters.map(entry => entry.species_id)).size;
        const progress = Math.round((Number(location.encounter_progress) || 0) * 100);
        const biasEntries = Object.entries(location.encounter_type_bias || {}).sort((left, right) => right[1] - left[1]);
        const highest = biasEntries[0]?.[1] ?? 1;
        const strongestBiases = biasEntries.filter(([, weight]) => weight === highest).map(([type]) => type).slice(0, 2);
        const finalBoss = encounters.some(entry => entry.is_final_boss);
        encounterMeta.textContent = finalBoss
            ? "final boss chamber · all d6 results are #0400"
            : `${uniqueCount} unique monsters · progression ${progress}% · strong type bias: ${strongestBiases.join(" / ") || "mixed"}`;
        for (const encounter of encounters) {
            const row = document.createElement("div");
            row.className = `encounter_row${encounter.is_final_boss ? " final_boss" : ""}`;
            row.dataset.type = encounter.type;
            const die = document.createElement("span");
            die.className = "encounter_die";
            die.textContent = String(encounter.roll);
            const copy = document.createElement("span");
            copy.className = "encounter_monster";
            const name = document.createElement("strong");
            name.textContent = `#${encounter.species_id} ${encounter.species_name}`;
            const detail = document.createElement("small");
            detail.textContent = `${encounter.type} · ${encounterDifficultyLabel(encounter.difficulty)}${encounter.is_final_boss ? " · final boss" : ""}`;
            copy.append(name, detail);
            row.append(die, copy);
            encounterTable.appendChild(row);
        }
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
        raise RuntimeError("could not replace PRESET_MAP")

    if "/* monster encounter table */" not in html:
        html = html.replace("\n</style>", ENCOUNTER_CSS + "\n</style>", 1)
    if 'id="encounter_table"' not in html:
        anchor = '                    <div id="art_filename" style="margin-top:7px;color:var(--muted);font-size:11px;overflow-wrap:anywhere"></div>\n'
        html = html.replace(anchor, anchor + ENCOUNTER_HTML, 1)
    html = html.replace(
        '    const STORAGE_KEY = "location_map_tool_v4_100_adventure_network_dense_v1";\n    const LEGACY_STORAGE_KEYS = [];',
        '    const STORAGE_KEY = "location_map_tool_v5_monster_encounters_v1";\n    const LEGACY_STORAGE_KEYS = ["location_map_tool_v4_100_adventure_network_dense_v1"];',
        1,
    )
    dom_anchor = '    const artFilename = document.getElementById("art_filename");\n'
    if 'document.getElementById("encounter_table")' not in html:
        html = html.replace(
            dom_anchor,
            dom_anchor
            + '    const encounterMeta = document.getElementById("encounter_meta");\n'
            + '    const encounterTable = document.getElementById("encounter_table");\n',
            1,
        )
    if "function normalizeEncounters(encounters)" not in html:
        html = html.replace("    function normalizeLocation(location) {\n", NORMALIZE_HELPERS + "    function normalizeLocation(location) {\n", 1)
    if "const presetLocation = PRESET_MAP.locations.find" not in html:
        html = html.replace(
            "    function normalizeLocation(location) {\n        const normalized = {\n",
            "    function normalizeLocation(location) {\n"
            "        const presetLocation = PRESET_MAP.locations.find(item => String(item.id) === String(location.id));\n"
            "        const encounterSource = Array.isArray(location.encounters) && location.encounters.length === 6 ? location : (presetLocation || location);\n"
            "        const normalized = {\n",
            1,
        )
    if "encounter_progress:" not in html.split("function normalizeLocation", 1)[1].split("function migrateParsedData", 1)[0]:
        html = html.replace(
            '            art: String(location.art || ""),\n            x: snap(Number.isFinite(location.x) ? location.x : 400),',
            '            art: String(location.art || ""),\n'
            '            encounters: normalizeEncounters(encounterSource.encounters),\n'
            '            encounter_progress: Number.isFinite(encounterSource.encounter_progress) ? encounterSource.encounter_progress : 0,\n'
            '            encounter_type_bias: normalizeEncounterBias(encounterSource.encounter_type_bias),\n'
            '            x: snap(Number.isFinite(location.x) ? location.x : 400),',
            1,
        )
    if "function renderEncounterTable(location)" not in html:
        html = html.replace("    function updateEditor() {\n", RENDER_HELPER + "    function updateEditor() {\n", 1)
    update_anchor = "        updateAutomaticArtPreview(location);\n"
    if "        renderEncounterTable(location);\n" not in html:
        html = html.replace(update_anchor, update_anchor + "        renderEncounterTable(location);\n", 1)
    html = html.replace("            version: 3,", "            version: 4,", 1)
    help_anchor = "                    The canvas is unbounded: drag empty space to pan in any direction. Use the mouse wheel to zoom.\n"
    if "Roll a six-sided die" not in html:
        html = html.replace(
            help_anchor,
            "                    Roll a six-sided die at a location and use the matching monster in its <b>monster_encounters</b> table. Encounter strength follows graph progression from the six starting villages toward Stillwater sanctum, with strong ecological type bias.<br><br>\n"
            + help_anchor,
            1,
        )
    return html


def write_manifest(map_data: dict, distribution: dict, monsters: list[dict]) -> None:
    locations = []
    for location in map_data["locations"]:
        unique = []
        seen = set()
        for entry in location["encounters"]:
            if entry["species_id"] in seen:
                continue
            seen.add(entry["species_id"])
            unique.append({key: value for key, value in entry.items() if key != "roll"})
        locations.append({
            "id": location["id"],
            "name": location["name"],
            "progress": location["encounter_progress"],
            "type_bias": location["encounter_type_bias"],
            "unique_monsters": unique,
            "d6": location["encounters"],
        })
    manifest = {
        "format": "book_of_loops_monster_encounters",
        "schema_version": 1,
        "rules": {
            "die": "d6",
            "maximum_unique_monsters_per_location": 6,
            "progression": "shortest graph distance from any starting village blended with shortest graph distance to Stillwater sanctum",
            "typing": "strong location-theme bias without hard type exclusion",
            "final_boss": {"location": "Stillwater sanctum", "species_id": "0400"},
        },
        "summary": {
            "locations": len(locations),
            "monsters": len(monsters),
            "ordinary_monsters_placed_at_least_once": 399,
            "top_type_bias_match_rate": distribution["top_bias_match_rate"],
            "difficulty_counts": dict(Counter(monster["difficulty"] for monster in monsters)),
        },
        "locations": locations,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    map_data = json.loads(MAP_PATH.read_text())
    if not isinstance(map_data.get("locations"), list) or not isinstance(map_data.get("links"), list):
        raise RuntimeError("location_map.json does not contain locations and links")
    monsters = load_monsters()
    distribution = distribute_encounters(map_data, monsters)
    map_data["version"] = max(4, int(map_data.get("version", 0) or 0))
    map_data["encounter_system"] = {
        "schema_version": 1,
        "die": "d6",
        "final_boss_location": BOSS_ID,
        "final_boss_species_id": FINAL_BOSS_SPECIES,
    }
    MAP_PATH.write_text(json.dumps(map_data, ensure_ascii=False, indent=2) + "\n")
    INDEX_PATH.write_text(patch_index(INDEX_PATH.read_text(), map_data))
    write_manifest(map_data, distribution, monsters)
    unique_counts = Counter(len({entry["species_id"] for entry in location["encounters"]}) for location in map_data["locations"])
    print(f"generated encounters for {len(map_data['locations'])} locations")
    print(f"unique monsters per location: {dict(sorted(unique_counts.items()))}")
    print(f"top ecological type-bias match rate: {distribution['top_bias_match_rate']:.1%}")
    print("Stillwater sanctum: d6 => #0400 duskervet on every face")


if __name__ == "__main__":
    main()
