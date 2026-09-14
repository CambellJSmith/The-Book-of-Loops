import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildAdjacency, buildCardIndex, getStartingLocations, FINAL_BOSS_SPECIES_ID, FINAL_LOCATION_ID } from "../engine.js";

const readJson = (relativeUrl) => JSON.parse(readFileSync(new URL(relativeUrl, import.meta.url), "utf8"));

test("repository data is playable by the digital engine", () => {
  const map = readJson("../../location_map.json");
  const cards = readJson("../../card_foundry/data/card_objects.json");
  const healing = readJson("../../healing_locations.json");
  const adjacency = buildAdjacency(map);
  const cardIndex = buildCardIndex(cards);
  const locationIds = new Set(map.locations.map((location) => String(location.id)));

  assert.equal(map.locations.length, 100);
  assert.equal(cardIndex.size, 400);
  assert.equal(getStartingLocations(map, adjacency).length, 6);
  assert.equal(healing.location_ids.length, 25);
  assert.equal(new Set(healing.location_ids).size, 25);
  assert.ok(healing.location_ids.every((id) => locationIds.has(String(id))));

  for (const location of map.locations) {
    assert.equal(location.encounters.length, 6, `${location.id} must have six d6 encounters`);
    for (const encounter of location.encounters) {
      assert.ok(cardIndex.has(String(encounter.species_id)), `${location.id} references missing species ${encounter.species_id}`);
    }
  }

  const boss = map.locations.find((location) => String(location.id) === FINAL_LOCATION_ID);
  assert.ok(boss);
  assert.ok(boss.encounters.every((encounter) => String(encounter.species_id) === FINAL_BOSS_SPECIES_ID));
});
