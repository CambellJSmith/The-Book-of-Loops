from __future__ import annotations  # Enables forward-compatible type annotations.

from typing import Any  # Describes portable move and card dictionaries.

STARTING_MANA = 0  # Every monster enters each battle with no stored mana.
MANA_PER_TURN = 1  # Every monster gains exactly one mana at the start of each of its turns.
ENEMY_FIRST_MOVE_ROLLS = range(1, 4)  # Enemy d6 results 1-3 select move one first.
ENEMY_SECOND_MOVE_ROLLS = range(4, 7)  # Enemy d6 results 4-6 select move two first.


def gain_turn_mana(current_mana: int) -> int:  # Applies the canonical start-of-turn mana gain.
    return max(0, int(current_mana)) + MANA_PER_TURN  # Keeps malformed negative values from reducing the battle resource.


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
        return alternate  # Prevents the enemy from wasting a turn while a legal attack exists.
    return None  # The enemy takes no attack and keeps its accumulated mana when neither move is affordable.


def move_two_is_stronger(card: dict[str, Any]) -> bool:  # Checks the canonical ordering of every monster's two attacks.
    moves = list(card.get("moves", []))  # Reads the complete move pair from portable card data.
    if len(moves) != 2:  # Rejects incomplete or expanded move sets.
        return False  # Keeps validation strict around the two-move game design.
    first, second = moves  # Names the weaker and stronger attack slots.
    return int(second.get("mana_cost", 0)) > int(first.get("mana_cost", 0)) and int(second.get("damage", 0)) > int(first.get("damage", 0))  # Requires move two to cost more mana and deal more damage.
