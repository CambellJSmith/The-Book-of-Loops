from __future__ import annotations

from collections import Counter

import location_encounters as core  # Reuses map progression, ecological scoring, card classification, and rendering helpers.


def guest_slot_priority(location_id: str, slot_index: int) -> int:
    spread_penalty = slot_index * 320_000  # Usually spreads guest encounters across locations before stacking a second guest into one place.
    return (core.stable_hash(f"blend_slot:{location_id}:{slot_index}") % 1_000_000) + spread_penalty  # Keeps the irregular spread deterministic.


def guest_monster_score(monster: dict, location: dict, home_id: str, progress: dict[str, float], biases: dict[str, dict[str, int]], appearance_counts: Counter[str]) -> float:
    location_id = str(location["id"])  # Reuses the canonical string id for all lookups.
    ecological_cost = core.placement_cost(monster, location, progress[location_id], biases[location_id])  # Preserves difficulty and biome relevance.
    home_distance = abs(progress[home_id] - progress[location_id]) * 70.0  # Prefers guest appearances at a similar point in the adventure.
    repeat_penalty = max(0, appearance_counts[monster["species_id"]] - 1) * 28.0  # Makes third appearances possible but less common than second appearances.
    wander_bias = (core.stable_hash(f"blend_wander:{monster['species_id']}") % 1000) / 1000.0 * 42.0  # Gives some species a stable tendency to recur more than others.
    local_jitter = (core.stable_hash(f"blend_pair:{monster['species_id']}:{location_id}") % 1000) / 1000.0 * 34.0  # Prevents every guest choice from being the mathematically perfect fit.
    return ecological_cost + home_distance + repeat_penalty + local_jitter - wander_bias  # Combines relevance with deliberately uneven recurrence.


def add_blended_guest_encounters(locations: list[dict], monsters: list[dict], progress: dict[str, float], biases: dict[str, dict[str, int]], capacities: dict[str, int], assignments: dict[str, list[dict]]) -> dict[str, int]:
    ordinary_monsters = [monster for monster in monsters if monster["species_id"] != core.FINAL_BOSS_SPECIES]  # Keeps the final boss exclusive to Stillwater sanctum.
    home_by_species = {monster["species_id"]: location["id"] for location in locations for monster in assignments[location["id"]]}  # Records each monster's one guaranteed canonical home.
    if len(home_by_species) != 399:  # Protects the canonical coverage guarantee before any blending is added.
        raise RuntimeError("canonical monster homes are incomplete before encounter blending")  # Rejects a malformed base distribution.
    appearance_counts: Counter[str] = Counter(home_by_species)  # Starts every ordinary monster at exactly one location appearance.
    open_slots: list[tuple[int, str]] = []  # Collects optional fourth-to-sixth slots without forcing all of them to be used.
    for location in locations:  # Scores every spare location slot independently.
        location_id = str(location["id"])  # Normalizes the location id once per location.
        spare_capacity = capacities[location_id] - len(assignments[location_id])  # Measures how many unique guest monsters can still fit here.
        for slot_index in range(spare_capacity):  # Creates deterministic candidates for each optional slot.
            open_slots.append((guest_slot_priority(location_id, slot_index), location_id))  # Gives later slots a soft penalty rather than banning them.
    open_slots.sort(key=lambda item: (item[0], item[1]))  # Makes the selected blend stable across rebuilds.
    target_guest_placements = min(len(open_slots), max(1, round(len(locations) * 0.35)))  # Adds a modest amount of overlap instead of filling every possible slot.
    location_by_id = {str(location["id"]): location for location in locations}  # Avoids repeated linear location searches during guest selection.
    guest_placements = 0  # Tracks successfully added cross-location appearances.
    for _, location_id in open_slots[:target_guest_placements]:  # Uses only the best irregular subset of available slots.
        location = location_by_id[location_id]  # Resolves the selected location once.
        existing_ids = {monster["species_id"] for monster in assignments[location_id]}  # Prevents a species being duplicated within one location's unique pool.
        allowed = core.allowed_difficulties(progress[location_id])  # Keeps guest encounters inside the same progression bands as canonical encounters.
        candidates = [
            monster
            for monster in ordinary_monsters
            if monster["species_id"] not in existing_ids
            and home_by_species[monster["species_id"]] != location_id
            and monster["difficulty"] in allowed
            and appearance_counts[monster["species_id"]] < 3
            and not (location_id in core.START_IDS and monster["difficulty"] != "easy")
        ]  # Builds only relevant, non-boss, non-duplicate guest candidates with a maximum of three total locations.
        if not candidates:  # Treats blending as optional instead of violating progression just to hit a quota.
            continue  # Leaves this spare slot unused when no suitable guest exists.
        chosen = min(
            candidates,
            key=lambda monster: guest_monster_score(monster, location, home_by_species[monster["species_id"]], progress, biases, appearance_counts),
        )  # Chooses a thematically relevant guest while retaining deterministic variation.
        assignments[location_id].append(chosen)  # Adds the extra appearance without changing the monster's canonical home.
        appearance_counts[chosen["species_id"]] += 1  # Updates recurrence pressure for later guest choices.
        guest_placements += 1  # Records one successful blended appearance.
    return {
        "guest_placements": guest_placements,
        "monsters_with_multiple_locations": sum(1 for count in appearance_counts.values() if count > 1),
        "max_locations_per_monster": max(appearance_counts.values(), default=1),
        "total_ordinary_location_appearances": sum(appearance_counts.values()),
    }  # Exposes blend statistics for the manifest and build log.


def distribute_encounters(map_data: dict, monsters: list[dict]) -> dict:
    progress = core.location_progress(map_data)  # Measures progression from the six starts toward the final sanctum.
    location_by_id = {str(location["id"]): location for location in map_data["locations"]}  # Indexes canonical locations.
    if core.BOSS_ID not in location_by_id or location_by_id[core.BOSS_ID].get("name") != "Stillwater sanctum":  # Protects the intended terminal chamber.
        raise RuntimeError("Stillwater sanctum is not the expected final location")  # Stops generation if the map's ending changed unexpectedly.

    ordinary_locations = [location for location in map_data["locations"] if location["id"] != core.BOSS_ID]  # Keeps the boss chamber outside ordinary allocation.
    ordinary_locations.sort(key=lambda location: (progress[location["id"]], location["id"]))  # Processes locations from early to late deterministically.
    biases = {location["id"]: core.type_bias(location) for location in ordinary_locations}  # Scores each biome/theme for all five monster types.
    capacities = {location["id"]: core.unique_capacity(progress[location["id"]]) for location in ordinary_locations}  # Allows three to six unique monsters depending on depth.
    if sum(capacities.values()) < 399:  # Requires enough room for every non-boss monster without requiring every optional slot to be filled.
        raise RuntimeError(f"ordinary location capacity is insufficient: {sum(capacities.values())}")  # Reports an invalid map/progression shape.

    assignments: dict[str, list[dict]] = {location["id"]: [] for location in ordinary_locations}  # Stores unique monsters per location.
    available = [monster for monster in monsters if monster["species_id"] != core.FINAL_BOSS_SPECIES]  # Reserves Duskervet for the final chamber.

    for location in ordinary_locations:  # Guarantees every ordinary location has a meaningful encounter pool.
        for _ in range(3):  # Seeds exactly three unique monsters before distributing optional fourth-to-sixth slots.
            chosen = core.choose_monster_for_location(available, location, progress[location["id"]], biases[location["id"]])  # Chooses the best progression/type fit still available.
            assignments[location["id"]].append(chosen)  # Claims the monster for this location.
            available.remove(chosen)  # Guarantees each ordinary monster receives exactly one canonical home.

    remaining_order = sorted(  # Places the remaining monsters into optional capacity in a stable order.
        available,
        key=lambda monster: (
            {"easy": 0, "ultra": 1, "medium": 2, "extra_hard": 3, "hard": 4}[monster["difficulty"]],
            monster["species_id"],
        ),
    )
    for monster in remaining_order:  # Distributes every monster not used by the three-per-location seed.
        location = core.choose_location_for_monster(monster, ordinary_locations, progress, biases, assignments, capacities)  # Finds its best remaining compatible home.
        assignments[location["id"]].append(monster)  # Fills one optional unique encounter slot.

    swap_count = core.optimize_assignments(ordinary_locations, progress, biases, assignments)  # Globally swaps canonical homes whenever ecology/progression improves.
    canonical_ids = [monster["species_id"] for values in assignments.values() for monster in values]  # Flattens the canonical ordinary distribution before adding guests.
    if len(canonical_ids) != 399 or len(set(canonical_ids)) != 399:  # Requires every non-boss monster exactly once at the canonical-home stage.
        raise RuntimeError("ordinary monsters were not assigned exactly one canonical home")  # Rejects omissions and duplicate canonical homes.
    blend_stats = add_blended_guest_encounters(ordinary_locations, monsters, progress, biases, capacities, assignments)  # Adds sparse relevant cross-location appearances into spare capacity.
    final_ids = {monster["species_id"] for values in assignments.values() for monster in values}  # Verifies blending retained complete ordinary coverage.
    if len(final_ids) != 399:  # Requires every canonical monster to remain represented after blending.
        raise RuntimeError("encounter blending lost ordinary monster coverage")  # Rejects accidental omissions introduced by future blending changes.
    if any(len(values) < 3 or len(values) > 6 for values in assignments.values()):  # Enforces the requested location encounter range after blending.
        raise RuntimeError("ordinary location unique encounter count is outside 3..6")  # Rejects malformed encounter pools.
    for start_id in core.START_IDS:  # Protects all six village starts after guest placement.
        if any(monster["difficulty"] != "easy" for monster in assignments[start_id]):  # Keeps the opening areas consistently forgiving.
            raise RuntimeError(f"starting location {start_id} contains a non-easy monster")  # Rejects accidental early difficulty spikes.

    boss = next(monster for monster in monsters if monster["species_id"] == core.FINAL_BOSS_SPECIES)  # Locates canonical #0400.
    for location in map_data["locations"]:  # Materializes progression metadata and d6 outcomes into every location record.
        location_id = str(location["id"])  # Normalizes the id before dictionary lookups.
        if location_id == core.BOSS_ID:  # Gives the final chamber one unique encounter regardless of die result.
            unique_monsters = [boss]  # Keeps Duskervet exclusive to the boss location.
            location_bias = core.type_bias(location)  # Retains the sanctum's thematic metadata.
        else:  # Uses the canonical-plus-guest pool everywhere else.
            unique_monsters = assignments[location_id]  # Includes sparse cross-location monster recurrence.
            location_bias = biases[location_id]  # Reuses the precomputed biome weights.
        location["encounter_progress"] = round(progress[location_id], 3)  # Stores readable graph-progression metadata.
        location["encounter_type_bias"] = dict(sorted(location_bias.items(), key=lambda item: (-item[1], item[0])))  # Exposes the thematic type weights for inspection.
        location["encounters"] = core.build_roll_table(location_id, unique_monsters, location_bias)  # Expands one-to-six unique monsters into six d6 faces.

    if any(len(location["encounters"]) != 6 for location in map_data["locations"]):  # Requires every location to resolve a d6 cleanly.
        raise RuntimeError("every location must have six d6 outcomes")  # Rejects incomplete die tables.
    if any(len({entry["species_id"] for entry in location["encounters"]}) > 6 for location in map_data["locations"]):  # Enforces the user's six-monster ceiling.
        raise RuntimeError("a location exceeds six unique monsters")  # Rejects oversized unique pools.
    boss_location = location_by_id[core.BOSS_ID]  # Reads the final generated chamber.
    if {entry["species_id"] for entry in boss_location["encounters"]} != {core.FINAL_BOSS_SPECIES}:  # Prevents ordinary monsters entering the finale.
        raise RuntimeError("Stillwater sanctum contains a non-boss encounter")  # Rejects contamination of the boss table.
    if any(entry["species_id"] == core.FINAL_BOSS_SPECIES for location in ordinary_locations for entry in location["encounters"]):  # Keeps #0400 exclusive to the sanctum.
        raise RuntimeError("final boss appears outside Stillwater sanctum")  # Rejects any ordinary-location Duskervet appearance.

    top_bias_matches = 0  # Counts all canonical and guest placements matching a location's strongest thematic type.
    ordinary_placements = 0  # Counts all ordinary location appearances after blending.
    themed_locations = 0  # Counts locations with a clearly dominant ecological theme.
    themed_locations_with_majority = 0  # Counts strongly themed locations whose monster pool follows that theme in the majority.
    for location in ordinary_locations:  # Audits ecological fit after canonical optimization and guest blending.
        weights = biases[location["id"]]  # Reads the location's five type weights.
        highest = max(weights.values())  # Finds the strongest ecological type score.
        preferred = {element for element, weight in weights.items() if weight == highest}  # Allows tied dominant themes.
        second_highest = sorted(weights.values(), reverse=True)[1]  # Measures whether the top theme is meaningfully dominant.
        values = assignments[location["id"]]  # Reads the final unique encounter pool including guests.
        preferred_count = sum(monster["type"] in preferred for monster in values)  # Counts dominant-theme monsters in the pool.
        if highest >= 7 and highest - second_highest >= 4:  # Treats a large thematic lead as a strong biome identity.
            themed_locations += 1  # Records one strongly themed location.
            if preferred_count >= (len(values) + 1) // 2:  # Requires at least half the unique pool to use the dominant type.
                themed_locations_with_majority += 1  # Records a themed location whose final encounters match its identity.
        for monster in values:  # Audits every final location appearance.
            ordinary_placements += 1  # Counts both canonical homes and guest appearances.
            if monster["type"] in preferred or highest == 1:  # Counts exact strongest-theme matches while treating unthemed locations as mixed.
                top_bias_matches += 1  # Records one ecological top-type match.

    return {
        "assignments": assignments,
        "progress": progress,
        "biases": biases,
        "top_bias_match_rate": round(top_bias_matches / max(1, ordinary_placements), 3),
        "themed_location_majority_rate": round(themed_locations_with_majority / max(1, themed_locations), 3),
        "swap_count": swap_count,
        **blend_stats,
    }  # Returns generated data, ecology metrics, and sparse blending statistics for the manifest/build log.
