from location_encounters import main  # Reuses the deterministic encounter generator and global ecological optimizer.

if __name__ == "__main__":  # Keeps the historical generator entry point stable for tooling.
    main()  # Regenerates location_map.json, monster_encounters.json, and the embedded map encounter UI.
