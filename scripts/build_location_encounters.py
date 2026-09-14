import healing_locations  # Keeps the browser map's healing-location UI synchronized after encounter regeneration.
import location_encounters as encounter_core  # Owns card reconstruction, graph progression, ecology scoring, map patching, and output rendering.
from location_encounter_distribution import distribute_encounters  # Owns the globally optimized three-to-six-monster placement pass.

encounter_core.distribute_encounters = distribute_encounters  # Replaces the legacy greedy distributor while preserving the stable generator entry point.

if __name__ == "__main__":  # Keeps automation and manual regeneration using the same command.
    encounter_core.main()  # Regenerates location_map.json, monster_encounters.json, and the embedded map encounter UI.
    healing_locations.apply_index_patch()  # Reapplies the canonical healing section after the embedded map is regenerated.
    healing_locations.validate_index()  # Fails immediately if the map tool no longer contains exactly the expected healing UI.
