import test from "node:test";
import assert from "node:assert/strict";
import {
  TEAM_SIZE_LIMIT,
  buildAdjacency,
  getStartingLocations,
  createMonsterInstance,
  grantRoundMana,
  canAffordMove,
  hasAffordableMove,
  chooseEnemyMove,
  compareSpeed,
  resolveSpeedTie,
  playerTurn,
  enemyTurn,
  healMonster,
  recruitmentSucceeded,
  rollD6,
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

test("d6 simulation maps random values to one through six", () => {
  assert.equal(rollD6(() => 0), 1);
  assert.equal(rollD6(() => 0.999999), 6);
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

test("both active monsters receive exactly one mana at round start", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance({ ...card, species_id: "0002" }, "e1");
  assert.equal(hasAffordableMove(player), false);
  assert.equal(hasAffordableMove(enemy), false);
  grantRoundMana(player, enemy);
  assert.equal(player.battle_mana, 1);
  assert.equal(enemy.battle_mana, 1);
  assert.equal(canAffordMove(player, 0), true);
  assert.equal(canAffordMove(player, 1), false);
});

test("player action spends existing mana and does not grant extra mana", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance({ ...card, species_id: "0002" }, "e1");
  grantRoundMana(player, enemy);
  const result = playerTurn(player, enemy, 0);
  assert.equal(result.damage, 20);
  assert.equal(player.battle_mana, 0);
  assert.equal(enemy.current_health, 60);
});

test("a monster with no affordable move skips without spending mana", () => {
  const expensiveCard = { ...card, moves: [{ name: "charge", mana_cost: 2, damage: 30 }, { name: "burst", mana_cost: 4, damage: 70 }] };
  const player = createMonsterInstance(expensiveCard, "m1");
  const enemy = createMonsterInstance(card, "e1");
  grantRoundMana(player, enemy);
  assert.equal(hasAffordableMove(player), false);
  const result = playerTurn(player, enemy, 0);
  assert.equal(result.moveIndex, null);
  assert.equal(result.damage, 0);
  assert.equal(player.battle_mana, 1);
});

test("player mana resets immediately when the enemy dies", () => {
  const player = createMonsterInstance(card, "m1");
  const enemy = createMonsterInstance({ ...card, species_id: "0002" }, "e1");
  player.battle_mana = 1;
  enemy.current_health = 20;
  const result = playerTurn(player, enemy, 0);
  assert.equal(result.killed, true);
  assert.equal(player.battle_mana, 0);
});

test("enemy move resolution consumes an explicit supplied d6 roll", () => {
  const enemy = createMonsterInstance(card, "e1");
  enemy.battle_mana = 1;
  assert.equal(chooseEnemyMove(enemy, 6), 0);
  assert.throws(() => chooseEnemyMove(enemy, 7), /between 1 and 6/);
});

test("speed order only asks for dice when speeds tie", () => {
  const player = createMonsterInstance(card, "m1");
  const fasterEnemy = createMonsterInstance({ ...card, speed: 120 }, "e1");
  const tiedEnemy = createMonsterInstance(card, "e2");
  assert.equal(compareSpeed(player, fasterEnemy), "enemy");
  assert.equal(compareSpeed(player, tiedEnemy), "tie");
  assert.equal(resolveSpeedTie(6, 2), "player");
  assert.equal(resolveSpeedTie(3, 3), "tie");
  assert.equal(resolveSpeedTie(1, 5), "enemy");
});

test("enemy action uses existing round mana and the clicked roll", () => {
  const enemy = createMonsterInstance(card, "e1");
  const player = createMonsterInstance(card, "m1");
  player.current_health = 20;
  grantRoundMana(player, enemy);
  const result = enemyTurn(enemy, player, 1);
  assert.equal(result.roll, 1);
  assert.equal(result.moveIndex, 0);
  assert.equal(result.killed, true);
  assert.equal(enemy.battle_mana, 0);
  assert.throws(() => enemyTurn(enemy, player, 0), /between 1 and 6/);
});

test("healing fully restores one monster", () => {
  const monster = createMonsterInstance(card, "m1");
  monster.current_health = 7;
  assert.equal(healMonster(monster), true);
  assert.equal(monster.current_health, 80);
});

test("recruitment resolves only the supplied clicked roll", () => {
  assert.deepEqual(recruitmentSucceeded(4), { roll: 4, success: false });
  assert.deepEqual(recruitmentSucceeded(5), { roll: 5, success: true });
  assert.throws(() => recruitmentSucceeded(9), /between 1 and 6/);
});

test("save parser rejects reserve-sized teams", () => {
  const team = Array.from({ length: 7 }, (_, index) => ({ instance_id: String(index) }));
  assert.throws(() => parseState(JSON.stringify({ team })), /six-monster/);
});
