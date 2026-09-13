from collections import Counter  # Checks exact difficulty and element distributions.
from pathlib import Path  # Locates the authored dataset independently of the working directory.
import json  # Reads the same cards used by the editor.

ROOT: Path = Path(__file__).resolve().parents[1]  # Resolves the project root.
cards: list[dict] = json.loads((ROOT / 'data/standalone_400.json').read_text())  # Loads the complete saved set.
assert len(cards) == 400  # Prevents an extra boss being appended to the requested total.
assert Counter(card['difficulty'] for card in cards) == {'easy': 133, 'medium': 133, 'hard': 133, 'boss': 1}  # Checks the equal ordinary groups and separate boss.
assert Counter(card['type'] for card in cards) == {element: 80 for element in ('fire', 'water', 'nature', 'light', 'dark')}  # Includes the boss in the original elemental distribution.
assert [card['species_id'] for card in cards] == [str(number).zfill(4) for number in range(1, 401)]  # Preserves the complete sequential species range.
assert len({card['species_name'] for card in cards}) == 400  # Rejects duplicate species identities.
assert all(not card['art'] and card['art_prompt'] for card in cards)  # Preserves the artwork-generation workflow.
for tier in ('easy', 'medium', 'hard'):  # Compares every member of each group rather than a sample.
    group: list[dict] = [card for card in cards if card['difficulty'] == tier]  # Selects the encounter group.
    profiles: set[tuple] = {(card['health'], card['speed'], tuple((move['mana_cost'], move['damage']) for move in card['moves'])) for card in group}  # Captures all numerically relevant direct-combat fields.
    assert len(profiles) == 1  # Requires complete statistical interchangeability within the group.

def duel(faster: dict, slower: dict) -> bool:  # Models a two-monster direct-damage encounter with the faster monster acting first.
    fast_hp: int = faster['health']  # Tracks the first combatant's remaining health.
    slow_hp: int = slower['health']  # Tracks the second combatant's remaining health.
    while fast_hp > 0:  # Continues until a combatant is defeated.
        slow_hp -= faster['moves'][1]['damage']  # Applies the stronger affordable attack.
        if slow_hp <= 0: return True  # Prevents a defeated monster from retaliating.
        fast_hp -= slower['moves'][1]['damage']  # Resolves the surviving monster's attack.
    return False  # Reports defeat of the first combatant.

for lower, upper in (('easy', 'medium'), ('medium', 'hard')):  # Checks both requested increases in encounter strength.
    low: dict = next(card for card in cards if card['difficulty'] == lower)  # Uses the group's verified common profile.
    high: dict = next(card for card in cards if card['difficulty'] == upper)  # Selects the next group's verified common profile.
    assert high['speed'] > low['speed'] and high['health'] == 2 * low['health']  # Requires a clear initiative and durability increase.
    assert high['moves'][1]['damage'] == 2 * low['moves'][1]['damage'] and duel(high, low)  # Verifies the stronger group wins under the documented rules.

def boss_encounter(team_size: int) -> tuple[bool, int, int]:  # Simulates focus fire against the boss without adding an application battle engine.
    boss: dict = cards[-1]  # Uses the actual final card.
    hard: dict = next(card for card in cards if card['difficulty'] == 'hard')  # Uses the group's interchangeable combat profile.
    health: list[int] = [hard['health']] * team_size  # Tracks each team member independently.
    boss_health: int = boss['health']  # Starts the encounter at full boss health.
    for round_number in range(1, 101):  # Bounds the reference simulation defensively.
        target: int = next((index for index, hp in enumerate(health) if hp > 0), -1)  # Focuses the first surviving monster.
        if target < 0: return False, round_number - 1, 0  # Stops when the entire team is defeated.
        health[target] -= boss['moves'][1]['damage']  # Resolves the faster boss's single-target attack first.
        for hp in health:  # Allows every surviving monster its action.
            if hp > 0: boss_health -= hard['moves'][1]['damage']  # Applies the player's stronger attack.
            if boss_health <= 0: return True, round_number, sum(value > 0 for value in health)  # Ends immediately when the boss is defeated.
    raise AssertionError('encounter did not finish')  # Rejects a stalled or invalid balance scenario.

assert cards[-1]['species_name'] == 'chronourobor' and cards[-1]['difficulty'] == 'boss'  # Keeps the time sovereign in the final slot.
assert all(not boss_encounter(size)[0] for size in (1, 2, 3))  # Requires more than a partial hard-monster team.
assert boss_encounter(4) == (True, 6, 1)  # Verifies the documented full-team win and remaining survivor.
print('PASS: 133 per ordinary tier; interchangeable stats; clear tier increases; 80 per type; time boss requires four hards in the reference model')  # Reports the actual checks without claiming general playtesting.
