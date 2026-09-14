import test from "node:test";
import assert from "node:assert/strict";
import {
  TEAM_SIZE_LIMIT,
  buildAdjacency,
  getStartingLocations,
  createMonsterInstance,
  canAffordMove,
  chooseEnemyMove,
  resolveSpeedOrder,
  playerTurn,
  enemyTurn,
  healMonster,
  recruitmentSucceeded,
  parseState,
} from "../engine.js";

const card = {
  species_id: "0001",
  species_name: "cindrel",
  type: "fire",
  health: 80,
  speed: 100,
  moves: [
    { name: "ember flick", mana_cost: 1, damage: 20 },
    { name: "flare spiral", mana_cost: 3, damage: 60 },
  ],
};

test("canonical team limit", () => {
  assert.equal(TEAM_SIZE_LIMIT, 6);
});

test("map adjacency and starting locations use degree one", () => {
  const map = {
    locations: [{ id: "loc_001" }, { id: "loc_002" }, { id: "loc_100" }],
    links: [{ source: "loc_001", target: "loc_002" }, { source: "loc_002", target: "loc_100" }],
  };
  const adjacency = buildAdjacency(map);
  assert.deepEqual(adjacency.get("loc_002").sort(), ["loc_001", "loc_100"]);
  assert.deepEqual(getStartingLocations(map, adjacency).map((location) => location.id), ["loc_001"]);
});

test("player receives mana at turn start and spends move cost", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance({ ...card, species_id: "0002" }, "e1");
  assert.equal(canAffordMove(player, 0, true), true);
  assert.equal(canAffordMove(player, 1, true), false);
  const result = playerTurn(player, enemy, 0);
  assert.equal(result.damage, 20);
  assert.equal(player.battle_mana, 0);
  assert.equal(enemy.current_health, 60);
});

test("player mana resets immediately when the enemy dies", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance({ ...card, species_id: "0002" }, "e1");
  player.battle_mana = 3;
  enemy.current_health = 20;
  const result = playerTurn(player, enemy, 0);
  assert.equal(result.killed, true);
  assert.equal(player.battle_mana, 0);
});

test("enemy falls back to affordable move", () => {
  const enemy = createMonsterInstance(card, "e1");
  enemy.battle_mana = 1;
  assert.equal(chooseEnemyMove(enemy, 6), 0);
});

test("speed ties reroll until resolved", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance(card, "e1");
  const values = [0.0, 0.0, 0.9, 0.1];
  const order = resolveSpeedOrder(player, enemy, () => values.shift());
  assert.equal(order.first, "player");
  assert.equal(order.rolls.length, 2);
});

test("enemy turn gains mana and can kill", () => {
  const enemy = createMonsterInstance(card, "e1");
  const player = createMonsterInstance(card, "m1");
  player.current_health = 20;
  const result = enemyTurn(enemy, player, () => 0.0);
  assert.equal(result.moveIndex, 0);
  assert.equal(result.killed, true);
});

test("healing fully restores one monster", () => {
  const monster = createMonsterInstance(card, "m1");
  monster.current_health = 7;
  assert.equal(healMonster(monster), true);
  assert.equal(monster.current_health, 80);
});

test("recruitment succeeds only on five or six", () => {
  assert.deepEqual(recruitmentSucceeded(() => 0.5), { roll: 4, success: false });
  assert.deepEqual(recruitmentSucceeded(() => 0.7), { roll: 5, success: true });
});

test("save parser rejects reserve-sized teams", () => {
  const team = Array.from({ length: 7 }, (_, index) => ({ instance_id: String(index) }));
  assert.throws(() => parseState(JSON.stringify({ team })), /six-monster/);
});
