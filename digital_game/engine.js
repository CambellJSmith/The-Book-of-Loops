export const TEAM_SIZE_LIMIT = 6;
export const FINAL_LOCATION_ID = "loc_100";
export const FINAL_BOSS_SPECIES_ID = "0400";

export function rollD6(random = Math.random) {
  return Math.floor(random() * 6) + 1;
}

export function buildAdjacency(mapData) {
  const adjacency = new Map((mapData.locations || []).map((location) => [String(location.id), []]));
  for (const link of mapData.links || []) {
    const source = String(link.source);
    const target = String(link.target);
    if (!adjacency.has(source) || !adjacency.has(target)) continue;
    adjacency.get(source).push(target);
    adjacency.get(target).push(source);
  }
  return adjacency;
}

export function getStartingLocations(mapData, adjacency = buildAdjacency(mapData)) {
  return (mapData.locations || []).filter((location) => {
    const id = String(location.id);
    return id !== FINAL_LOCATION_ID && (adjacency.get(id) || []).length === 1;
  });
}

export function buildCardIndex(cardData) {
  return new Map((cardData.cards || []).map((card) => [String(card.species_id), card]));
}

export function encounterForRoll(location, roll) {
  const encounters = Array.isArray(location?.encounters) ? location.encounters : [];
  return encounters.find((entry) => Number(entry.roll) === Number(roll)) || encounters[Number(roll) - 1] || null;
}

export function createMonsterInstance(card, instanceId) {
  return {
    instance_id: String(instanceId),
    species_id: String(card.species_id),
    species_name: String(card.species_name),
    type: String(card.type),
    max_health: Number(card.health),
    current_health: Number(card.health),
    speed: Number(card.speed),
    moves: (card.moves || []).map((move) => ({
      name: String(move.name),
      mana_cost: Number(move.mana_cost),
      damage: Number(move.damage),
    })),
    battle_mana: 0,
  };
}

export function resetBattleMana(team) {
  for (const monster of team) monster.battle_mana = 0;
}

export function canAffordMove(monster, moveIndex, includeTurnGain = true) {
  const move = monster?.moves?.[moveIndex];
  if (!move) return false;
  const available = Number(monster.battle_mana || 0) + (includeTurnGain ? 1 : 0);
  return available >= Number(move.mana_cost || 0);
}

export function chooseEnemyMove(enemy, roll) {
  const preferred = Number(roll) <= 3 ? 0 : 1;
  const alternate = 1 - preferred;
  if (canAffordMove(enemy, preferred, false)) return preferred;
  if (canAffordMove(enemy, alternate, false)) return alternate;
  return null;
}

export function resolveSpeedOrder(player, enemy, random = Math.random) {
  if (player.speed > enemy.speed) return { first: "player", rolls: [] };
  if (enemy.speed > player.speed) return { first: "enemy", rolls: [] };
  const rolls = [];
  while (true) {
    const playerRoll = rollD6(random);
    const enemyRoll = rollD6(random);
    rolls.push({ player: playerRoll, enemy: enemyRoll });
    if (playerRoll > enemyRoll) return { first: "player", rolls };
    if (enemyRoll > playerRoll) return { first: "enemy", rolls };
  }
}

export function applyDamage(monster, damage) {
  monster.current_health = Math.max(0, Number(monster.current_health) - Math.max(0, Number(damage)));
  return monster.current_health === 0;
}

export function healMonster(monster) {
  const wasDamaged = monster.current_health < monster.max_health;
  monster.current_health = monster.max_health;
  return wasDamaged;
}

export function enemyTurn(enemy, target, random = Math.random) {
  enemy.battle_mana = Number(enemy.battle_mana || 0) + 1;
  const roll = rollD6(random);
  const moveIndex = chooseEnemyMove(enemy, roll);
  if (moveIndex === null) return { roll, moveIndex: null, damage: 0, killed: false };
  const move = enemy.moves[moveIndex];
  enemy.battle_mana -= move.mana_cost;
  const killed = applyDamage(target, move.damage);
  return { roll, moveIndex, damage: move.damage, killed };
}

export function playerTurn(player, enemy, moveIndex) {
  player.battle_mana = Number(player.battle_mana || 0) + 1;
  const move = player.moves[moveIndex];
  if (!move || player.battle_mana < move.mana_cost) {
    return { moveIndex: null, damage: 0, killed: false };
  }
  player.battle_mana -= move.mana_cost;
  const killed = applyDamage(enemy, move.damage);
  return { moveIndex, damage: move.damage, killed };
}

export function recruitmentSucceeded(random = Math.random) {
  const roll = rollD6(random);
  return { roll, success: roll >= 5 };
}

export function isHealingLocation(locationId, healingLocationIds) {
  return healingLocationIds instanceof Set && healingLocationIds.has(String(locationId));
}

export function serializeState(state) {
  return JSON.stringify(state);
}

export function parseState(serialized) {
  const state = JSON.parse(serialized);
  if (!state || typeof state !== "object" || !Array.isArray(state.team)) throw new Error("invalid save data");
  if (state.team.length > TEAM_SIZE_LIMIT) throw new Error("save exceeds six-monster team limit");
  return state;
}
