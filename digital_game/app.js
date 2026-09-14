import {
  TEAM_SIZE_LIMIT,
  FINAL_LOCATION_ID,
  FINAL_BOSS_SPECIES_ID,
  buildAdjacency,
  getStartingLocations,
  buildCardIndex,
  encounterForRoll,
  createMonsterInstance,
  resetBattleMana,
  grantRoundMana,
  canAffordMove,
  hasAffordableMove,
  compareSpeed,
  resolveSpeedTie,
  playerTurn,
  enemyTurn,
  recruitmentSucceeded,
  healMonster,
  isHealingLocation,
  rollD6,
  serializeState,
  parseState,
} from "./engine.js";

const STORAGE_KEY = "book_of_loops_digital_save_v1";
const MAX_LOG_ENTRIES = 160;
const DICE_FACES = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];

let mapData = null;
let cardData = null;
let cardIndex = null;
let locationById = null;
let adjacency = null;
let healingLocationIds = null;
let healingNote = "You can choose to fully heal one of your monsters.";
let state = null;

const ui = {
  locationId: document.getElementById("location_id"),
  locationName: document.getElementById("location_name"),
  locationDescription: document.getElementById("location_description"),
  locationArt: document.getElementById("location_art"),
  locationArtFallback: document.getElementById("location_art_fallback"),
  healingSection: document.getElementById("healing_section"),
  healingChoices: document.getElementById("healing_choices"),
  travelChoices: document.getElementById("travel_choices"),
  phaseLabel: document.getElementById("phase_label"),
  battleEmpty: document.getElementById("battle_empty"),
  battleContent: document.getElementById("battle_content"),
  combatants: document.querySelector(".combatants"),
  playerCombatant: document.getElementById("player_combatant"),
  enemyCombatant: document.getElementById("enemy_combatant"),
  diceResult: document.getElementById("dice_result"),
  battlePrompt: document.getElementById("battle_prompt"),
  battleControls: document.getElementById("battle_controls"),
  recruitPanel: document.getElementById("recruit_panel"),
  endingPanel: document.getElementById("ending_panel"),
  teamCount: document.getElementById("team_count"),
  teamList: document.getElementById("team_list"),
  gameLog: document.getElementById("game_log"),
  startDialog: document.getElementById("start_dialog"),
  startNewButton: document.getElementById("start_new_button"),
  continueButton: document.getElementById("continue_button"),
  loadError: document.getElementById("load_error"),
  saveButton: document.getElementById("save_button"),
  exportButton: document.getElementById("export_button"),
  importInput: document.getElementById("import_input"),
  newGameButton: document.getElementById("new_game_button"),
  clearLogButton: document.getElementById("clear_log_button"),
};

function allocateInstanceId(prefix = "m") {
  const value = state.next_instance_id || 1;
  state.next_instance_id = value + 1;
  return `${prefix}${String(value).padStart(4, "0")}`;
}

function currentLocation() {
  return locationById?.get(String(state?.location_id)) || null;
}

function activeMonster() {
  return state?.team?.find((monster) => monster.instance_id === state.active_instance_id) || state?.team?.[0] || null;
}

function appendLog(text) {
  if (!state) return;
  state.log ??= [];
  state.log.push(String(text));
  if (state.log.length > MAX_LOG_ENTRIES) state.log.splice(0, state.log.length - MAX_LOG_ENTRIES);
}

function saveState() {
  if (!state) return;
  localStorage.setItem(STORAGE_KEY, serializeState(state));
}

function commitState() {
  saveState();
  render();
}

function normalizeLoadedState(loaded) {
  loaded.version = 2;
  loaded.log ??= [];
  loaded.next_instance_id ??= 1;
  loaded.last_roll ??= null;
  loaded.pending_move_index ??= null;
  loaded.round_order ??= null;
  loaded.speed_tie_player_roll ??= null;
  loaded.pending_recruit_species_id ??= null;
  loaded.encounter_roll ??= null;
  loaded.recruit_roll ??= null;
  loaded.healing_available ??= false;
  loaded.battle_round ??= 0;
  return loaded;
}

function createFromSpecies(speciesId, prefix = "m") {
  const card = cardIndex.get(String(speciesId));
  if (!card) throw new Error(`missing card data for species ${speciesId}`);
  return createMonsterInstance(card, allocateInstanceId(prefix));
}

function recordRoll(label, value) {
  state.last_roll = { label: String(label), value: Number(value) };
}

function clearRoundTracking() {
  state.pending_move_index = null;
  state.round_order = null;
  state.speed_tie_player_roll = null;
}

function newGame() {
  const starts = getStartingLocations(mapData, adjacency);
  if (starts.length !== 6) throw new Error(`expected six starting villages, found ${starts.length}`);

  state = {
    version: 2,
    next_instance_id: 1,
    location_id: null,
    team: [],
    active_instance_id: null,
    phase: "start_roll",
    enemy: null,
    pending_recruit: null,
    pending_recruit_species_id: null,
    healing_available: false,
    encounter_roll: null,
    recruit_roll: null,
    pending_move_index: null,
    round_order: null,
    speed_tie_player_roll: null,
    battle_round: 0,
    last_roll: null,
    battle_count: 0,
    visits: 0,
    log: [],
  };

  appendLog("A new loop begins. Click the die to roll for your starting village.");
  ui.startDialog.close();
  commitState();
}

function loadSavedState() {
  const serialized = localStorage.getItem(STORAGE_KEY);
  if (!serialized) return false;
  state = normalizeLoadedState(parseState(serialized));
  ui.startDialog.close();
  render();
  return true;
}

function rollStartingVillage() {
  if (state.phase !== "start_roll") return;
  const starts = getStartingLocations(mapData, adjacency);
  const roll = rollD6();
  recordRoll("starting village", roll);
  const location = starts[roll - 1];
  if (!location) throw new Error(`no starting village exists for roll ${roll}`);
  state.location_id = String(location.id);
  state.visits = 1;
  state.phase = "starter_roll";
  appendLog(`Starting village roll: ${roll}. You begin at ${location.name}.`);
  appendLog("Click the die again to roll for your starter monster.");
  commitState();
}

function rollStarterMonster() {
  if (state.phase !== "starter_roll") return;
  const location = currentLocation();
  if (!location) return;
  const roll = rollD6();
  recordRoll("starter monster", roll);
  const starterEncounter = encounterForRoll(location, roll);
  if (!starterEncounter) throw new Error(`starting village ${location.name} has no encounter for roll ${roll}`);
  const starter = createFromSpecies(starterEncounter.species_id);
  state.team.push(starter);
  state.active_instance_id = starter.instance_id;
  state.phase = "travel";
  appendLog(`Starter roll: ${roll}. ${starter.species_name} #${starter.species_id} joins your team at full Health.`);
  appendLog("Choose a travel route. Your starter is not battled at the starting village.");
  commitState();
}

function travelTo(locationId) {
  if (state.phase !== "travel") return;
  const targetId = String(locationId);
  if (!(adjacency.get(String(state.location_id)) || []).includes(targetId)) return;
  const location = locationById.get(targetId);
  if (!location) return;

  state.location_id = targetId;
  state.visits = Number(state.visits || 0) + 1;
  state.healing_available = isHealingLocation(targetId, healingLocationIds);
  state.pending_recruit = null;
  state.pending_recruit_species_id = null;
  state.recruit_roll = null;
  state.encounter_roll = null;
  state.enemy = null;
  resetBattleMana(state.team);
  clearRoundTracking();
  state.phase = "encounter_roll";

  appendLog(`Travelled to ${location.name}. Click the die to roll this location's encounter.`);
  if (state.healing_available) appendLog("This location can fully heal one carried monster during this visit.");
  commitState();
}

function rollEncounter() {
  if (state.phase !== "encounter_roll") return;
  const location = currentLocation();
  if (!location) return;
  const roll = rollD6();
  recordRoll("encounter", roll);
  const encounter = encounterForRoll(location, roll);
  if (!encounter) throw new Error(`${location.name} has no encounter for roll ${roll}`);
  const enemy = createFromSpecies(encounter.species_id, "e");
  enemy.instance_id = `enemy-${Number(state.battle_count || 0) + 1}`;
  state.battle_count = Number(state.battle_count || 0) + 1;
  state.enemy = enemy;
  state.encounter_roll = roll;
  state.phase = "prebattle";
  appendLog(`Encounter roll: ${roll}. ${enemy.species_name} #${enemy.species_id} appears with ${enemy.current_health} Health.`);
  commitState();
}

function chooseActive(instanceId) {
  const monster = state.team.find((entry) => entry.instance_id === String(instanceId));
  if (!monster) return;
  state.active_instance_id = monster.instance_id;
  commitState();
}

function beginBattle() {
  if (state.phase !== "prebattle" || !state.enemy || !activeMonster()) return;
  resetBattleMana(state.team);
  state.enemy.battle_mana = 0;
  state.battle_round = 0;
  clearRoundTracking();
  appendLog(`${activeMonster().species_name} enters battle. Both monsters begin with 0 Mana.`);
  beginBattleRound();
  commitState();
}

function beginBattleRound() {
  const player = activeMonster();
  const enemy = state.enemy;
  if (!player || !enemy) return;

  while (true) {
    clearRoundTracking();
    state.battle_round = Number(state.battle_round || 0) + 1;
    grantRoundMana(player, enemy);
    appendLog(`Round ${state.battle_round} begins. ${player.species_name} and ${enemy.species_name} each gain 1 Mana.`);

    const playerCanAct = hasAffordableMove(player);
    const enemyCanAct = hasAffordableMove(enemy);
    if (!playerCanAct) appendLog(`${player.species_name} cannot afford either move and skips this round.`);
    if (!enemyCanAct) appendLog(`${enemy.species_name} cannot afford either move and skips this round.`);

    if (!playerCanAct && !enemyCanAct) {
      appendLog("Both monsters skip. The next round begins.");
      continue;
    }

    if (!playerCanAct) {
      state.round_order = "enemy_only";
      state.phase = "enemy_move_roll";
      appendLog(`${enemy.species_name} can act this round. Click the die to roll which move it attempts.`);
      return;
    }

    state.phase = "battle";
    return;
  }
}

function completeBattleRound() {
  clearRoundTracking();
  beginBattleRound();
}

function logPlayerTurn(player, result) {
  if (result.moveIndex === null) {
    appendLog(`${player.species_name} cannot afford a move and skips its action.`);
    return;
  }
  const move = player.moves[result.moveIndex];
  appendLog(`${player.species_name} uses ${move.name} for ${result.damage} damage. Enemy Health: ${state.enemy.current_health}/${state.enemy.max_health}.`);
}

function logEnemyTurn(enemy, result) {
  if (result.moveIndex === null) {
    appendLog(`${enemy.species_name} cannot afford either move and skips its action, keeping its Mana.`);
    return;
  }
  const move = enemy.moves[result.moveIndex];
  appendLog(`${enemy.species_name} rolled ${result.roll} and uses ${move.name} for ${result.damage} damage. ${activeMonster()?.species_name || "Your monster"} Health: ${activeMonster()?.current_health ?? 0}.`);
}

function handlePlayerDeath(deadInstanceId) {
  const index = state.team.findIndex((monster) => monster.instance_id === deadInstanceId);
  if (index < 0) return;
  const [dead] = state.team.splice(index, 1);
  appendLog(`${dead.species_name} has died and is permanently discarded.`);
  clearRoundTracking();
  if (state.team.length === 0) {
    state.active_instance_id = null;
    state.phase = "game_over";
    appendLog("You have no monsters left. This loop ends here.");
    return;
  }
  state.active_instance_id = state.team[0].instance_id;
  state.phase = "replacement";
  appendLog("Choose another carried monster to continue the battle.");
}

function finishEnemyDefeat() {
  const enemy = state.enemy;
  if (!enemy) return;
  appendLog(`${enemy.species_name} is defeated.`);
  clearRoundTracking();

  if (String(state.location_id) === FINAL_LOCATION_ID && enemy.species_id === FINAL_BOSS_SPECIES_ID) {
    state.enemy = null;
    state.phase = "victory";
    appendLog("Duskervet falls. You have reached the Stillwater sanctum and broken through the final battle.");
    return;
  }

  state.pending_recruit_species_id = enemy.species_id;
  state.enemy = null;
  state.recruit_roll = null;
  state.phase = "recruitment_roll";
  appendLog("Click the die to roll for recruitment. A 5 or 6 recruits the defeated monster.");
}

function resolveRoundOrder(first) {
  const player = activeMonster();
  const enemy = state.enemy;
  if (!player || !enemy) return;
  state.round_order = first;

  if (first === "player") {
    const result = playerTurn(player, enemy, state.pending_move_index);
    logPlayerTurn(player, result);
    if (result.killed) {
      finishEnemyDefeat();
      return;
    }
    if (!hasAffordableMove(enemy)) {
      completeBattleRound();
      return;
    }
  }

  state.phase = "enemy_move_roll";
  appendLog(`${enemy.species_name}'s action. Click the die to roll which affordable move it attempts.`);
}

function startRound(moveIndex) {
  if (state.phase !== "battle") return;
  const player = activeMonster();
  const enemy = state.enemy;
  if (!player || !enemy || !canAffordMove(player, moveIndex)) return;

  state.pending_move_index = moveIndex;
  state.round_order = null;
  state.speed_tie_player_roll = null;

  if (!hasAffordableMove(enemy)) {
    state.round_order = "player_only";
    const result = playerTurn(player, enemy, moveIndex);
    logPlayerTurn(player, result);
    if (result.killed) finishEnemyDefeat();
    else completeBattleRound();
    commitState();
    return;
  }

  const speedOrder = compareSpeed(player, enemy);
  if (speedOrder === "tie") {
    state.phase = "speed_tie_player_roll";
    appendLog(`Speed is tied at ${player.speed}. Click the die to roll your Speed tie-break.`);
  } else {
    resolveRoundOrder(speedOrder);
  }
  commitState();
}

function rollPlayerSpeedTie() {
  if (state.phase !== "speed_tie_player_roll") return;
  const roll = rollD6();
  recordRoll("your Speed tie-break", roll);
  state.speed_tie_player_roll = roll;
  state.phase = "speed_tie_enemy_roll";
  appendLog(`Speed tie: you rolled ${roll}. Now click the die to roll for the enemy.`);
  commitState();
}

function rollEnemySpeedTie() {
  if (state.phase !== "speed_tie_enemy_roll") return;
  const enemyRoll = rollD6();
  recordRoll("enemy Speed tie-break", enemyRoll);
  const playerRoll = Number(state.speed_tie_player_roll);
  const result = resolveSpeedTie(playerRoll, enemyRoll);
  appendLog(`Speed tie: enemy rolled ${enemyRoll}.`);
  if (result === "tie") {
    appendLog(`Both rolled ${enemyRoll}. Click to roll your Speed die again.`);
    state.speed_tie_player_roll = null;
    state.phase = "speed_tie_player_roll";
  } else {
    appendLog(`${result === "player" ? "You act" : "The enemy acts"} first this round.`);
    resolveRoundOrder(result);
  }
  commitState();
}

function rollEnemyMove() {
  if (state.phase !== "enemy_move_roll") return;
  const player = activeMonster();
  const enemy = state.enemy;
  if (!player || !enemy) return;
  const roll = rollD6();
  recordRoll("enemy move", roll);
  const enemyResult = enemyTurn(enemy, player, roll);
  logEnemyTurn(enemy, enemyResult);

  if (enemyResult.killed) {
    handlePlayerDeath(player.instance_id);
    commitState();
    return;
  }

  if (state.round_order === "enemy") {
    const result = playerTurn(player, enemy, state.pending_move_index);
    logPlayerTurn(player, result);
    if (result.killed) {
      finishEnemyDefeat();
      commitState();
      return;
    }
  }

  completeBattleRound();
  commitState();
}

function rollRecruitment() {
  if (state.phase !== "recruitment_roll" || !state.pending_recruit_species_id) return;
  const roll = rollD6();
  recordRoll("recruitment", roll);
  const recruitment = recruitmentSucceeded(roll);
  state.recruit_roll = roll;
  const speciesId = state.pending_recruit_species_id;
  state.pending_recruit_species_id = null;

  if (!recruitment.success) {
    const card = cardIndex.get(String(speciesId));
    appendLog(`Recruitment roll: ${roll}. ${card?.species_name || "The defeated monster"} is not recruited.`);
    state.phase = "travel";
    commitState();
    return;
  }

  const recruit = createFromSpecies(speciesId);
  appendLog(`Recruitment roll: ${roll}. ${recruit.species_name} can join at full Health.`);
  if (state.team.length < TEAM_SIZE_LIMIT) {
    state.team.push(recruit);
    appendLog(`${recruit.species_name} joins your team. Team size: ${state.team.length}/${TEAM_SIZE_LIMIT}.`);
    state.phase = "travel";
    commitState();
    return;
  }

  state.pending_recruit = recruit;
  state.phase = "discard";
  appendLog("Your team is full. Discard the new recruit or one monster you are already carrying.");
  commitState();
}

function continueReplacement(instanceId) {
  if (state.phase !== "replacement") return;
  const monster = state.team.find((entry) => entry.instance_id === String(instanceId));
  if (!monster) return;
  state.active_instance_id = monster.instance_id;
  monster.battle_mana = 0;
  appendLog(`${monster.species_name} enters the ongoing battle with 0 Mana. A new battle round begins.`);
  beginBattleRound();
  commitState();
}

function discardPendingRecruit() {
  if (state.phase !== "discard" || !state.pending_recruit) return;
  appendLog(`${state.pending_recruit.species_name} is discarded. Your existing six-monster team is unchanged.`);
  state.pending_recruit = null;
  state.phase = "travel";
  commitState();
}

function replaceTeamMember(instanceId) {
  if (state.phase !== "discard" || !state.pending_recruit) return;
  const index = state.team.findIndex((monster) => monster.instance_id === String(instanceId));
  if (index < 0) return;
  const discarded = state.team[index];
  const recruit = state.pending_recruit;
  state.team.splice(index, 1, recruit);
  if (state.active_instance_id === discarded.instance_id) state.active_instance_id = recruit.instance_id;
  state.pending_recruit = null;
  state.phase = "travel";
  appendLog(`${discarded.species_name} is discarded. ${recruit.species_name} takes its place at full Health.`);
  commitState();
}

function useHealing(instanceId) {
  if (!state.healing_available || !["encounter_roll", "prebattle", "travel"].includes(state.phase)) return;
  const monster = state.team.find((entry) => entry.instance_id === String(instanceId));
  if (!monster || monster.current_health >= monster.max_health) return;
  healMonster(monster);
  state.healing_available = false;
  appendLog(`${monster.species_name} is fully healed at ${currentLocation().name}.`);
  commitState();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function monsterCardHtml(monster) {
  if (!monster) return "";
  const healthPercent = monster.max_health > 0 ? Math.max(0, Math.min(100, monster.current_health / monster.max_health * 100)) : 0;
  const manaPercent = Math.min(100, Number(monster.battle_mana || 0) / 6 * 100);
  return `
    <div class="monster-name"><span>${escapeHtml(monster.species_name)} <small>#${escapeHtml(monster.species_id)}</small></span><span class="type-chip type-${escapeHtml(monster.type)}">${escapeHtml(monster.type)}</span></div>
    <div class="stat-row"><span>Health</span><span>${monster.current_health} / ${monster.max_health}</span></div>
    <div class="health-track"><div class="health-fill" style="width:${healthPercent}%"></div></div>
    <div class="stat-row"><span>Mana</span><span>${monster.battle_mana || 0}</span></div>
    <div class="mana-track"><div class="mana-fill" style="width:${manaPercent}%"></div></div>
    <div class="stat-row"><span>Speed</span><span>${monster.speed}</span></div>
    <div class="move-summary">${monster.moves.map((move) => `<div><span>${escapeHtml(move.name)}</span><span>${move.mana_cost} Mana · ${move.damage} dmg</span></div>`).join("")}</div>`;
}

function renderLocation() {
  const location = currentLocation();
  if (!location) {
    ui.locationId.textContent = "—";
    ui.locationName.textContent = "the loop awaits";
    ui.locationDescription.textContent = "Roll the die to determine where your run begins.";
    ui.locationArt.removeAttribute("src");
    ui.locationArt.style.display = "none";
    ui.locationArtFallback.style.display = "block";
    ui.locationArtFallback.textContent = "starting location not rolled yet";
    ui.healingSection.hidden = true;
    ui.healingChoices.replaceChildren();
    ui.travelChoices.replaceChildren();
    const blocked = document.createElement("span");
    blocked.className = "muted";
    blocked.textContent = "roll your starting village first";
    ui.travelChoices.append(blocked);
    return;
  }

  ui.locationId.textContent = String(location.id);
  ui.locationName.textContent = String(location.name);
  ui.locationDescription.textContent = String(location.description || "");
  ui.locationArtFallback.textContent = "no location art";
  ui.locationArt.style.display = "none";
  ui.locationArtFallback.style.display = "block";
  ui.locationArt.alt = `${location.name} artwork`;
  ui.locationArt.onerror = () => {
    ui.locationArt.style.display = "none";
    ui.locationArtFallback.style.display = "block";
  };
  ui.locationArt.onload = () => {
    ui.locationArt.style.display = "block";
    ui.locationArtFallback.style.display = "none";
  };
  const art = String(location.art || "").trim();
  ui.locationArt.src = art.startsWith("data:image/") ? art : `../${encodeURIComponent(location.name)}.png`;

  const canHeal = state.healing_available && ["encounter_roll", "prebattle", "travel"].includes(state.phase);
  ui.healingSection.hidden = !canHeal;
  ui.healingChoices.replaceChildren();
  if (canHeal) {
    const damaged = state.team.filter((monster) => monster.current_health < monster.max_health);
    if (!damaged.length) {
      const note = document.createElement("span");
      note.className = "muted";
      note.textContent = "all carried monsters are already at full Health";
      ui.healingChoices.append(note);
    } else {
      for (const monster of damaged) {
        const button = document.createElement("button");
        button.className = "heal-button";
        button.innerHTML = `<span>heal ${escapeHtml(monster.species_name)}</span><span>${monster.current_health} → ${monster.max_health}</span>`;
        button.addEventListener("click", () => useHealing(monster.instance_id));
        ui.healingChoices.append(button);
      }
    }
  }

  ui.travelChoices.replaceChildren();
  const neighbors = adjacency.get(String(location.id)) || [];
  if (state.phase !== "travel") {
    const blocked = document.createElement("span");
    blocked.className = "muted";
    blocked.textContent = state.phase === "victory" ? "the loop is complete" : "resolve the current step before travelling";
    ui.travelChoices.append(blocked);
    return;
  }
  for (const neighborId of neighbors) {
    const neighbor = locationById.get(neighborId);
    if (!neighbor) continue;
    const button = document.createElement("button");
    button.className = "route-button";
    button.innerHTML = `<span>${escapeHtml(neighbor.name)}</span><span>${escapeHtml(neighbor.id)}</span>`;
    button.addEventListener("click", () => travelTo(neighborId));
    ui.travelChoices.append(button);
  }
}

function renderRollButton(label, handler, detail = "") {
  const action = document.createElement("div");
  action.className = "dice-roll-action";
  const button = document.createElement("button");
  button.className = "dice-button";
  button.type = "button";
  button.innerHTML = `<span class="dice-button-icon">◆</span><span>${escapeHtml(label)}</span>`;
  button.addEventListener("click", handler);
  action.append(button);
  if (detail) {
    const note = document.createElement("span");
    note.className = "dice-help";
    note.textContent = detail;
    action.append(note);
  }
  ui.battleControls.append(action);
}

function renderDiceResult() {
  if (!state.last_roll) {
    ui.diceResult.hidden = true;
    ui.diceResult.replaceChildren();
    return;
  }
  const value = Number(state.last_roll.value);
  ui.diceResult.hidden = false;
  ui.diceResult.innerHTML = `<span class="dice-face" aria-hidden="true">${DICE_FACES[value] || value}</span><div><span class="dice-result-label">${escapeHtml(state.last_roll.label)}</span><strong>${value}</strong></div>`;
}

function renderBattle() {
  ui.phaseLabel.textContent = String(state.phase).replaceAll("_", " ");
  ui.recruitPanel.hidden = true;
  ui.endingPanel.hidden = true;
  ui.battleControls.replaceChildren();
  ui.battlePrompt.textContent = "";
  renderDiceResult();

  const showEnemy = Boolean(state.enemy);
  ui.combatants.hidden = !showEnemy;
  if (showEnemy) {
    ui.playerCombatant.innerHTML = monsterCardHtml(activeMonster());
    ui.enemyCombatant.innerHTML = monsterCardHtml(state.enemy);
  } else {
    ui.playerCombatant.innerHTML = "";
    ui.enemyCombatant.innerHTML = "";
  }

  ui.battleEmpty.hidden = true;
  ui.battleContent.hidden = false;

  if (state.phase === "travel") {
    ui.battleEmpty.hidden = false;
    ui.battleContent.hidden = true;
    return;
  }

  if (state.phase === "start_roll") {
    ui.battlePrompt.textContent = "Roll one six-sided die to choose which of the six starting villages begins this run.";
    renderRollButton("roll starting village d6", rollStartingVillage, "The result 1–6 maps directly to the six starting villages.");
    return;
  }

  if (state.phase === "starter_roll") {
    ui.battlePrompt.textContent = `You begin at ${currentLocation()?.name || "your starting village"}. Roll its encounter table to determine your starter.`;
    renderRollButton("roll starter d6", rollStarterMonster, "The rolled monster joins at full Health and is not battled here.");
    return;
  }

  if (state.phase === "encounter_roll") {
    ui.battlePrompt.textContent = `You arrived at ${currentLocation()?.name || "a new location"}. Roll its d6 encounter table.`;
    renderRollButton("roll encounter d6", rollEncounter, "The result selects exactly one face of this location's encounter table.");
    return;
  }

  if (state.phase === "prebattle") {
    ui.battlePrompt.textContent = `Encounter roll ${state.encounter_roll}. Choose the monster that will enter battle.`;
    const grid = document.createElement("div");
    grid.className = "select-grid";
    for (const monster of state.team) {
      const button = document.createElement("button");
      button.className = `select-monster${monster.instance_id === state.active_instance_id ? " active" : ""}`;
      button.innerHTML = `<strong>${escapeHtml(monster.species_name)}</strong><br><small>${monster.current_health}/${monster.max_health} Health · Speed ${monster.speed}</small>`;
      button.addEventListener("click", () => chooseActive(monster.instance_id));
      grid.append(button);
    }
    ui.battleControls.append(grid);
    const begin = document.createElement("button");
    begin.className = "primary-button";
    begin.textContent = "begin battle";
    begin.addEventListener("click", beginBattle);
    ui.battleControls.append(begin);
    return;
  }

  if (state.phase === "battle") {
    const player = activeMonster();
    ui.battlePrompt.textContent = `Round ${state.battle_round}. Both active monsters have already gained 1 Mana at the start of this round. Choose an affordable move.`;
    player.moves.forEach((move, index) => {
      const button = document.createElement("button");
      button.className = "move-button";
      button.disabled = !canAffordMove(player, index);
      button.innerHTML = `<strong>${escapeHtml(move.name)}</strong><span class="cost">${move.mana_cost} Mana</span><span class="damage">${move.damage} dmg</span>`;
      button.addEventListener("click", () => startRound(index));
      ui.battleControls.append(button);
    });
    return;
  }

  if (state.phase === "speed_tie_player_roll") {
    ui.battlePrompt.textContent = `Speed is tied at ${activeMonster()?.speed}. Roll your tie-break die.`;
    renderRollButton("roll your Speed d6", rollPlayerSpeedTie, "After this result, you will separately roll the enemy's Speed die.");
    return;
  }

  if (state.phase === "speed_tie_enemy_roll") {
    ui.battlePrompt.textContent = `You rolled ${state.speed_tie_player_roll}. Now roll the enemy's tie-break die.`;
    renderRollButton("roll enemy Speed d6", rollEnemySpeedTie, "If both dice match, both rolls must be clicked again.");
    return;
  }

  if (state.phase === "enemy_move_roll") {
    ui.battlePrompt.textContent = `${state.enemy?.species_name || "The enemy"} has enough Mana to act this round. Roll the enemy move die: 1–3 selects Move 1, 4–6 selects Move 2; if that move is too expensive, it uses the other affordable move.`;
    renderRollButton("roll enemy move d6", rollEnemyMove, "The enemy cannot choose a move until you click this roll.");
    return;
  }

  if (state.phase === "replacement") {
    ui.battlePrompt.textContent = "Your active monster died. Choose another carried monster; the enemy keeps its current Health and Mana.";
    const grid = document.createElement("div");
    grid.className = "select-grid";
    for (const monster of state.team) {
      const button = document.createElement("button");
      button.className = "select-monster";
      button.innerHTML = `<strong>${escapeHtml(monster.species_name)}</strong><br><small>${monster.current_health}/${monster.max_health} Health</small>`;
      button.addEventListener("click", () => continueReplacement(monster.instance_id));
      grid.append(button);
    }
    ui.battleControls.append(grid);
    return;
  }

  if (state.phase === "recruitment_roll") {
    const card = cardIndex.get(String(state.pending_recruit_species_id));
    ui.battlePrompt.textContent = `${card?.species_name || "The defeated monster"} is defeated. Roll d6: 5–6 recruits it at full Health; 1–4 leaves it behind.`;
    renderRollButton("roll recruitment d6", rollRecruitment, "Recruitment is not resolved until you click the die.");
    return;
  }

  if (state.phase === "discard" && state.pending_recruit) {
    ui.battleContent.hidden = true;
    ui.recruitPanel.hidden = false;
    ui.recruitPanel.replaceChildren();
    const heading = document.createElement("strong");
    heading.textContent = `team full · ${state.pending_recruit.species_name} was recruited`;
    const note = document.createElement("p");
    note.textContent = "You may carry only six monsters. There is no storage or reserve team. Discard the new recruit, or replace one monster you are already carrying.";
    const discard = document.createElement("button");
    discard.textContent = `discard new ${state.pending_recruit.species_name}`;
    discard.addEventListener("click", discardPendingRecruit);
    ui.recruitPanel.append(heading, note, discard);
    const grid = document.createElement("div");
    grid.className = "select-grid";
    for (const monster of state.team) {
      const button = document.createElement("button");
      button.className = "select-monster";
      button.innerHTML = `<strong>replace ${escapeHtml(monster.species_name)}</strong><br><small>${monster.current_health}/${monster.max_health} Health</small>`;
      button.addEventListener("click", () => replaceTeamMember(monster.instance_id));
      grid.append(button);
    }
    ui.recruitPanel.append(grid);
    return;
  }

  if (state.phase === "victory") {
    ui.battleContent.hidden = true;
    ui.endingPanel.hidden = false;
    ui.endingPanel.innerHTML = `<h2>the loop is broken</h2><p>Duskervet has been defeated at the Stillwater sanctum.</p><p>You completed this run with ${state.team.length} monster${state.team.length === 1 ? "" : "s"} still carried.</p>`;
    return;
  }

  if (state.phase === "game_over") {
    ui.battleContent.hidden = true;
    ui.endingPanel.hidden = false;
    ui.endingPanel.innerHTML = `<h2>the loop closes</h2><p>Every monster in your team has died. Start a new loop to try again.</p>`;
  }
}

function renderTeam() {
  ui.teamCount.textContent = `${state.team.length} / ${TEAM_SIZE_LIMIT}`;
  ui.teamList.replaceChildren();
  for (const monster of state.team) {
    const card = document.createElement("article");
    card.className = `team-card${monster.instance_id === state.active_instance_id ? " active" : ""}`;
    const healthPercent = Math.max(0, Math.min(100, monster.current_health / monster.max_health * 100));
    card.innerHTML = `
      <div class="team-card-top"><span class="team-card-name">${escapeHtml(monster.species_name)}</span><span class="type-chip type-${escapeHtml(monster.type)}">${escapeHtml(monster.type)}</span></div>
      <div class="team-card-id">#${escapeHtml(monster.species_id)} · ${escapeHtml(monster.instance_id)}</div>
      <div class="stat-row"><span>Health</span><span>${monster.current_health} / ${monster.max_health}</span></div>
      <div class="health-track"><div class="health-fill" style="width:${healthPercent}%"></div></div>
      <div class="stat-row"><span>Speed ${monster.speed}</span><span>Mana ${monster.battle_mana || 0}</span></div>`;
    ui.teamList.append(card);
  }
}

function renderLog() {
  ui.gameLog.replaceChildren();
  (state.log || []).forEach((entry, index) => {
    const row = document.createElement("div");
    row.className = "log-entry";
    const number = document.createElement("span");
    number.className = "log-index";
    number.textContent = String(index + 1).padStart(3, "0");
    const text = document.createElement("span");
    text.className = "log-text";
    text.textContent = entry;
    row.append(number, text);
    ui.gameLog.append(row);
  });
  ui.gameLog.scrollTop = ui.gameLog.scrollHeight;
}

function render() {
  if (!state || !mapData) return;
  renderLocation();
  renderBattle();
  renderTeam();
  renderLog();
}

function exportSave() {
  if (!state) return;
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "book_of_loops_save.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

async function importSave(file) {
  if (!file) return;
  try {
    const imported = normalizeLoadedState(parseState(await file.text()));
    if (imported.location_id !== null && !locationById.has(String(imported.location_id))) throw new Error("save references an unknown location");
    for (const monster of imported.team) {
      if (!cardIndex.has(String(monster.species_id))) throw new Error(`save references unknown species ${monster.species_id}`);
    }
    state = imported;
    saveState();
    ui.startDialog.close();
    render();
  } catch (error) {
    alert(`Could not import save: ${error.message}`);
  } finally {
    ui.importInput.value = "";
  }
}

function bindUi() {
  ui.startNewButton.addEventListener("click", newGame);
  ui.continueButton.addEventListener("click", loadSavedState);
  ui.saveButton.addEventListener("click", () => {
    saveState();
    appendLog("Game saved locally.");
    renderLog();
  });
  ui.exportButton.addEventListener("click", exportSave);
  ui.importInput.addEventListener("change", () => importSave(ui.importInput.files?.[0]));
  ui.newGameButton.addEventListener("click", () => {
    if (!state || confirm("Start a new loop? This replaces the current local save.")) newGame();
  });
  ui.clearLogButton.addEventListener("click", () => {
    if (!state) return;
    state.log = [];
    commitState();
  });
}

async function loadGameData() {
  const [mapResponse, cardsResponse, healingResponse] = await Promise.all([
    fetch("../location_map.json"),
    fetch("../card_foundry/data/card_objects.json"),
    fetch("../healing_locations.json"),
  ]);
  if (!mapResponse.ok) throw new Error(`could not load location_map.json (${mapResponse.status})`);
  if (!cardsResponse.ok) throw new Error(`could not load card_objects.json (${cardsResponse.status})`);
  if (!healingResponse.ok) throw new Error(`could not load healing_locations.json (${healingResponse.status})`);

  mapData = await mapResponse.json();
  cardData = await cardsResponse.json();
  const healingData = await healingResponse.json();
  healingLocationIds = new Set((healingData.location_ids || []).map(String));
  healingNote = String(healingData.note || healingNote);
  const healingText = document.querySelector("#healing_section p");
  if (healingText) healingText.textContent = healingNote;

  adjacency = buildAdjacency(mapData);
  locationById = new Map(mapData.locations.map((location) => [String(location.id), location]));
  cardIndex = buildCardIndex(cardData);
  if (locationById.size !== 100) throw new Error(`expected 100 locations, found ${locationById.size}`);
  if (cardIndex.size !== 400) throw new Error(`expected 400 monsters, found ${cardIndex.size}`);
  if (healingLocationIds.size !== 25) throw new Error(`expected 25 healing locations, found ${healingLocationIds.size}`);
  if (getStartingLocations(mapData, adjacency).length !== 6) throw new Error("map no longer contains exactly six starting villages");
}

async function init() {
  bindUi();
  try {
    await loadGameData();
    ui.locationName.textContent = "ready";
    ui.locationDescription.textContent = "Start or continue a loop.";
    ui.continueButton.hidden = !localStorage.getItem(STORAGE_KEY);
    ui.startDialog.showModal();
  } catch (error) {
    ui.loadError.hidden = false;
    ui.loadError.textContent = `${error.message}. Run this through a local web server rather than opening the HTML file directly.`;
    ui.startNewButton.disabled = true;
    ui.continueButton.disabled = true;
    ui.startDialog.showModal();
  }
}

init();
