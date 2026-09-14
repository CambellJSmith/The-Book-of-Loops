import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(resolve(here, "../app.js"), "utf8");

function functionBody(name) {
  const start = app.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `missing ${name}`);
  const next = app.indexOf("\nfunction ", start + 1);
  return app.slice(start, next === -1 ? app.length : next);
}

test("every gameplay d6 is owned by an explicit roll handler", () => {
  const rollHandlers = [
    "rollStartingVillage",
    "rollStarterMonster",
    "rollEncounter",
    "rollPlayerSpeedTie",
    "rollEnemySpeedTie",
    "rollEnemyMove",
    "rollRecruitment",
  ];
  for (const name of rollHandlers) assert.match(functionBody(name), /rollD6\(\)/, `${name} must simulate its d6 only after that handler is invoked`);
  const totalRollCalls = [...app.matchAll(/rollD6\(\)/g)].length;
  assert.equal(totalRollCalls, rollHandlers.length, "rollD6 must not be called anywhere except explicit roll handlers");
});

test("new game, travel and move selection do not roll automatically", () => {
  for (const name of ["newGame", "travelTo", "startRound", "resolveRoundOrder", "finishEnemyDefeat"]) {
    assert.doesNotMatch(functionBody(name), /rollD6\(\)/, `${name} must stop and wait for a click-driven roll phase`);
  }
});

test("roll controls are actual click actions", () => {
  const renderer = functionBody("renderRollButton");
  assert.match(renderer, /addEventListener\("click", handler\)/);
  for (const phase of ["start_roll", "starter_roll", "encounter_roll", "speed_tie_player_roll", "speed_tie_enemy_roll", "enemy_move_roll", "recruitment_roll"]) {
    assert.match(app, new RegExp(`state\\.phase === \\"${phase}\\"`), `missing rendered roll phase ${phase}`);
  }
});