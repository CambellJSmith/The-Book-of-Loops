from __future__ import annotations  # Enables forward-compatible type annotations.

from typing import Any  # Describes portable move and card dictionaries.

STARTING_MANA = 0  # Every monster enters each battle with no stored mana.
MANA_PER_ROUND = 1  # Both active monsters gain exactly one mana at the start of every battle round.
MANA_PER_TURN = MANA_PER_ROUND  # Backward-compatible alias for older tooling; round-start gain is canonical.
TEAM_SIZE_LIMIT = 6  # The player can carry at most six monsters and has no reserve storage.
ENEMY_FIRST_MOVE_ROLLS = range(1, 4)  # Enemy d6 results 1-3 select move one first.
ENEMY_SECOND_MOVE_ROLLS = range(4, 7)  # Enemy d6 results 4-6 select move two first.


def gain_round_mana(current_mana: int) -> int:  # Applies the canonical start-of-round mana gain to one active monster.
    return max(0, int(current_mana)) + MANA_PER_ROUND  # Keeps malformed negative values from reducing the battle resource.


def gain_turn_mana(current_mana: int) -> int:  # Preserves the old helper name for callers outside the canonical rules path.
    return gain_round_mana(current_mana)  # Mana is no longer granted separately inside each monster action.


def can_afford_move(current_mana: int, move: dict[str, Any]) -> bool:  # Checks whether a monster can legally use one move now.
    return max(0, int(current_mana)) >= max(0, int(move.get("mana_cost", 0)))  # Compares accumulated mana with the printed move cost.


def spend_move_mana(current_mana: int, move: dict[str, Any]) -> int:  # Pays for a move after affordability has been established.
    if not can_afford_move(current_mana, move):  # Rejects impossible attacks instead of allowing negative mana.
        raise ValueError("monster does not have enough mana for that move")  # Gives callers an explicit illegal-move failure.
    return int(current_mana) - int(move.get("mana_cost", 0))  # Removes exactly the printed mana cost from the current pool.


def enemy_move_index(roll: int, current_mana: int, moves: list[dict[str, Any]]) -> int | None:  # Resolves the enemy d6 choice against available mana.
    if roll not in range(1, 7):  # Requires a genuine d6 result.
        raise ValueError("enemy move roll must be between 1 and 6")  # Prevents accidental non-d6 values from silently choosing an attack.
    if len(moves) != 2:  # Requires the canonical two-move monster format.
        raise ValueError("enemy monster must have exactly two moves")  # Keeps move-selection behavior deterministic.
    preferred = 0 if roll in ENEMY_FIRST_MOVE_ROLLS else 1  # Maps 1-3 to move one and 4-6 to move two.
    alternate = 1 - preferred  # Identifies the other move for the affordability fallback.
    if can_afford_move(current_mana, moves[preferred]):  # Uses the rolled move whenever the monster can pay for it.
        return preferred  # Returns the selected zero-based move index.
    if can_afford_move(current_mana, moves[alternate]):  # Falls back when only the other move is currently affordable.
        return alternate  # Uses the legal attack instead of wasting a turn after a high-cost roll.
    return None  # A monster with no affordable move skips its action and keeps accumulated mana.


def recruitment_requires_discard(current_team_size: int) -> bool:  # Checks whether accepting a recruited monster forces a discard choice.
    return max(0, int(current_team_size)) >= TEAM_SIZE_LIMIT  # A full six-monster team must discard either the recruit or one carried monster.


def move_two_is_stronger(card: dict[str, Any]) -> bool:  # Checks the canonical ordering of every monster's two attacks.
    moves = list(card.get("moves", []))  # Reads the complete move pair from portable card data.
    if len(moves) != 2:  # Rejects incomplete or expanded move sets.
        return False  # Keeps validation strict around the two-move game design.
    first, second = moves  # Names the weaker and stronger attack slots.
    return int(second.get("mana_cost", 0)) > int(first.get("mana_cost", 0)) and int(second.get("damage", 0)) > int(first.get("damage", 0))  # Requires move two to cost more mana and deal more damage.
