from __future__ import annotations

import location_encounters as core  # Reuses map progression, ecological scoring, card classification, and rendering helpers.


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

    swap_count = core.optimize_assignments(ordinary_locations, progress, biases, assignments)  # Globally swaps placements whenever ecology/progression improves.
    placed_ids = [monster["species_id"] for values in assignments.values() for monster in values]  # Flattens the canonical ordinary distribution.
    if len(placed_ids) != 399 or len(set(placed_ids)) != 399:  # Requires every non-boss monster exactly once.
        raise RuntimeError("ordinary monsters were not placed exactly once")  # Rejects omissions and duplicate canonical homes.
    if any(len(values) < 3 or len(values) > 6 for values in assignments.values()):  # Enforces the requested location encounter range.
        raise RuntimeError("ordinary location unique encounter count is outside 3..6")  # Rejects malformed encounter pools.
    for start_id in core.START_IDS:  # Protects all six village starts.
        if any(monster["difficulty"] != "easy" for monster in assignments[start_id]):  # Keeps the opening areas consistently forgiving.
            raise RuntimeError(f"starting location {start_id} contains a non-easy monster")  # Rejects accidental early difficulty spikes.

    boss = next(monster for monster in monsters if monster["species_id"] == core.FINAL_BOSS_SPECIES)  # Locates canonical #0400.
    for location in map_data["locations"]:  # Materializes progression metadata and d6 outcomes into every location record.
        location_id = str(location["id"])
        if location_id == core.BOSS_ID:  # Gives the final chamber one unique encounter regardless of die result.
            unique_monsters = [boss]
            location_bias = core.type_bias(location)
        else:  # Uses the globally optimized unique pool everywhere else.
            unique_monsters = assignments[location_id]
            location_bias = biases[location_id]
        location["encounter_progress"] = round(progress[location_id], 3)  # Stores readable graph-progression metadata.
        location["encounter_type_bias"] = dict(sorted(location_bias.items(), key=lambda item: (-item[1], item[0])))  # Exposes the thematic type weights for inspection.
        location["encounters"] = core.build_roll_table(location_id, unique_monsters, location_bias)  # Expands one-to-six unique monsters into six d6 faces.

    if any(len(location["encounters"]) != 6 for location in map_data["locations"]):  # Requires every location to resolve a d6 cleanly.
        raise RuntimeError("every location must have six d6 outcomes")
    if any(len({entry["species_id"] for entry in location["encounters"]}) > 6 for location in map_data["locations"]):  # Enforces the user's six-monster ceiling.
        raise RuntimeError("a location exceeds six unique monsters")
    boss_location = location_by_id[core.BOSS_ID]  # Reads the final generated chamber.
    if {entry["species_id"] for entry in boss_location["encounters"]} != {core.FINAL_BOSS_SPECIES}:  # Prevents ordinary monsters entering the finale.
        raise RuntimeError("Stillwater sanctum contains a non-boss encounter")
    if any(entry["species_id"] == core.FINAL_BOSS_SPECIES for location in ordinary_locations for entry in location["encounters"]):  # Keeps #0400 exclusive to the sanctum.
        raise RuntimeError("final boss appears outside Stillwater sanctum")

    top_bias_matches = 0  # Counts placements matching a location's strongest thematic type.
    ordinary_placements = 0  # Counts all 399 ordinary canonical homes.
    themed_locations = 0  # Counts locations with a clearly dominant ecological theme.
    themed_locations_with_majority = 0  # Counts strongly themed locations whose monster pool follows that theme in the majority.
    for location in ordinary_locations:  # Audits ecological fit after global optimization.
        weights = biases[location["id"]]
        highest = max(weights.values())
        preferred = {element for element, weight in weights.items() if weight == highest}
        second_highest = sorted(weights.values(), reverse=True)[1]
        values = assignments[location["id"]]
        preferred_count = sum(monster["type"] in preferred for monster in values)
        if highest >= 7 and highest - second_highest >= 4:  # Treats a large thematic lead as a strong biome identity.
            themed_locations += 1
            if preferred_count >= (len(values) + 1) // 2:  # Requires at least half the unique pool to use the dominant type.
                themed_locations_with_majority += 1
        for monster in values:
            ordinary_placements += 1
            if monster["type"] in preferred or highest == 1:  # Counts exact strongest-theme matches while treating unthemed locations as mixed.
                top_bias_matches += 1

    return {
        "assignments": assignments,
        "progress": progress,
        "biases": biases,
        "top_bias_match_rate": round(top_bias_matches / max(1, ordinary_placements), 3),
        "themed_location_majority_rate": round(themed_locations_with_majority / max(1, themed_locations), 3),
        "swap_count": swap_count,
    }  # Returns both generated data and quality metrics for the manifest/build log.
