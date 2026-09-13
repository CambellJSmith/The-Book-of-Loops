from collections import Counter  # Checks uniqueness and equal type and difficulty counts.
from pathlib import Path  # Resolves the source concepts and generated collection.
from typing import TypedDict  # Describes the portable generation records.
import json  # Serializes editor-ready cards.
import uuid  # Assigns reproducible record identities.

class Move(TypedDict):  # Describes a complete attack.
    name: str  # Stores the authored move name.
    mana_cost: int  # Stores its resource cost.
    damage: int  # Stores its direct damage.

class Card(TypedDict):  # Describes a complete standalone monster.
    id: str  # Identifies the durable editor record.
    species_id: str  # Preserves sequential leading-zero numbering.
    species_name: str  # Stores its unique species name.
    type: str  # Selects the elemental category.
    difficulty: str  # Stores the encounter progression band.
    is_final_boss: bool  # Marks the one climactic game encounter.
    art: str  # Leaves artwork ready for attachment.
    art_prompt: str  # Retains the self-contained generation brief.
    art_width: int  # Reserves the intended portrait width.
    art_height: int  # Reserves the intended portrait height.
    art_zoom: int  # Sets initial crop magnification.
    art_x: int  # Centers the future artwork horizontally.
    art_y: int  # Centers the future artwork vertically.
    health: int  # Stores monster durability.
    speed: int  # Stores monster initiative.
    moves: list[Move]  # Stores its two attacks.
    revision: int  # Marks the initial persisted version.

ROOT: Path = Path(__file__).resolve().parents[1]  # Locates the project independently of the working directory.
TYPES: tuple[str, ...] = ('fire', 'water', 'nature', 'light', 'dark')  # Defines the interleaved element order.
DIFFICULTIES: tuple[str, ...] = ('easy', 'medium', 'hard', 'extra_hard', 'ultra')  # Defines the requested encounter bands in ascending order.
STYLE: str = ('STYLE: 1122 × 1402 px portrait artwork; roughly 4:5 portrait aspect ratio; museum-quality traditional watercolor illustration on cold-pressed cotton paper; layered transparent washes; luminous glazing; controlled wet-on-wet transitions; fine dry-brush texture; natural pigment granulation; crisp value-defined edges; subtle watercolor blooms; carefully modeled volume; rich harmonious color; refined storybook concept-art finish; soft grounded contact shadow; generous clean off-white paper field; centered single-creature presentation; high-resolution scan quality.')  # Keeps the shared visual treatment independent of creature anatomy.
PALETTES: dict[str, str] = {'fire': 'ember orange, copper, brick red and warm charcoal', 'water': 'deep teal, cerulean, frosted blue and pearl', 'nature': 'moss green, warm bark brown, fresh leaf green and botanical accent colors', 'light': 'warm ivory, pale gold, opal and luminous pastel highlights', 'dark': 'charcoal, deep indigo, muted violet and restrained silver highlights'}  # Harmonizes each element without changing the authored materials.
PROFILES: tuple[tuple[int, int], ...] = ((80, 100), (90, 90), (100, 80), (110, 70), (120, 60), (130, 50), (140, 40), (150, 30), (160, 20), (115, 65))  # Supplies the original tank-versus-speed identities before tier scaling.
STAT_TOTALS: dict[str, int] = {'easy': 150, 'medium': 190, 'hard': 235, 'extra_hard': 285, 'ultra': 340}  # Raises the combined health-and-speed budget at every tier.
MOVE_BANDS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {'easy': ((1, 20), (2, 40)), 'medium': ((1, 30), (3, 70)), 'hard': ((2, 55), (3, 90)), 'extra_hard': ((2, 70), (4, 125)), 'ultra': ((3, 100), (5, 180))}  # Raises move cost, damage and damage efficiency through progression.
POSITIVE_TERMS: tuple[tuple[str, int], ...] = (('colossal', 10), ('giant', 6), ('huge', 6), ('massive', 6), ('fortress', 5), ('ancient', 4), ('guardian', 4), ('golem', 4), ('dragon', 6), ('basilisk', 6), ('tyrant', 5), ('rhinoceros', 4), ('lion', 3), ('walrus', 3), ('crocodilian', 4), ('sharklike', 4), ('scorpion', 4), ('raptor', 3), ('buffalo', 4), ('bear', 3), ('armoured', 3), ('armored', 3), ('heavy', 3), ('muscular', 3), ('strong', 3), ('broad shouldered', 2), ('basalt', 2), ('obsidian', 2), ('iron', 1), ('molten', 2), ('lava', 4), ('storm', 3), ('abyss', 3), ('whirlpool', 3), ('geyser', 3), ('furnace', 3), ('solar', 2), ('oracle', 3), ('knight', 2), ('sabre toothed', 4), ('carnivorous', 4), ('hornet', 3), ('serpent', 2))  # Scores visual and anatomical threat cues.
NEGATIVE_TERMS: tuple[tuple[str, int], ...] = (('thimble sized', -7), ('tiny', -6), ('small', -4), ('little', -4), ('delicate', -3), ('gentle', -3), ('cheerful', -3), ('playful', -3), ('friendly', -3), ('soft', -2), ('plump', -1), ('round', -1), ('curious', -1), ('sprite', -2), ('compact', -1))  # Scores diminutive and gentle cues toward early tiers.
DANGEROUS_MOVE_TERMS: tuple[tuple[str, int], ...] = (('crush', 4), ('eruption', 4), ('avalanche', 5), ('detonation', 5), ('inferno', 5), ('eclipse', 3), ('upheaval', 5), ('roar', 3), ('barrage', 4), ('charge', 2), ('torrent', 2), ('deluge', 4), ('quake', 4), ('blast', 4), ('cyclone', 4), ('stampede', 4), ('furnace', 4), ('blaze', 3), ('squall', 3), ('downpour', 3), ('gale', 2), ('ram', 2), ('pounce', 2), ('constrict', 3), ('sting', 2), ('slash', 2), ('beam', 2), ('surge', 1), ('rush', 1), ('wave', 1))  # Scores destructive authored move language.
GENTLE_MOVE_TERMS: tuple[tuple[str, int], ...] = (('tap', -2), ('flick', -2), ('glint', -2), ('nudge', -2), ('hop', -1), ('clink', -1), ('dab', -1), ('bop', -1), ('whisk', -1), ('skip', -1), ('flutter', -1), ('step', -1))  # Scores low-threat authored move language.
FINAL_BOSS_SUBJECT: str = 'SUBJECT: duskervet, an original dark-type final-boss monster. Depict a colossal four-legged sovereign formed from layered smoky indigo fur and articulated black-violet shadow armour, with six sweeping silver whisker-horns, a crown of suspended eclipse rings, a luminous violet core set deep in its chest, polished obsidian claws and nine vast fan-shaped shadow tails arcing behind it like a broken celestial wheel. Each tail carries fine silver runic seams and starless black eyespots, while a mantle of slow violet darkness rises behind its shoulders into a regal silhouette. Present Duskervet planted in a dominant, imposing stance with its full anatomy clearly readable, immense scale communicated through monumental proportions, broad weight-bearing limbs and controlled supernatural presence. Keep every tail individually legible and make the crown, chest core, whisker-horns and central face the unmistakable focal hierarchy. Render the creature as the singular climactic opponent of the world, with refined watercolor material separation, a soft grounded contact shadow and generous clean off-white paper surrounding the complete silhouette.'  # Defines card four hundred as the singular final boss.

def normalized_words(value: str) -> str:  # Makes whole-word and multi-word threat matching predictable.
    return f" {' '.join(''.join(character if character.isalnum() else ' ' for character in value.lower()).split())} "  # Normalizes punctuation and repeated whitespace.

def weighted_score(text: str, terms: tuple[tuple[str, int], ...]) -> int:  # Totals authored threat cues present in one description.
    haystack: str = normalized_words(text)  # Normalizes the source text once per scoring pass.
    return sum(weight for term, weight in terms if normalized_words(term) in haystack)  # Adds each matching cue at most once.

def threat_score(card: Card) -> int:  # Estimates relative encounter threat from concept and move language.
    if card['species_id'] == '0400':  # Reserves the final card for the strongest normal-band position.
        return 1_000_000  # Guarantees Duskervet sorts into Ultra.
    subject: str = card['art_prompt'].split('SUBJECT:', 1)[-1]  # Ignores the repeated watercolor style boilerplate.
    concept: str = f"{card['species_name']} {subject}"  # Combines physical and magical creature cues.
    moves: str = f"{card['moves'][0]['name']} {card['moves'][1]['name']}"  # Combines both attack names for combat cues.
    return weighted_score(concept, POSITIVE_TERMS) + weighted_score(concept, NEGATIVE_TERMS) + weighted_score(moves, DANGEROUS_MOVE_TERMS) + weighted_score(moves, GENTLE_MOVE_TERMS)  # Produces one deterministic content-aware score.

def round_to_five(value: float) -> int:  # Keeps generated combat values visually simple.
    return int(value / 5 + 0.5) * 5  # Mirrors positive JavaScript Math.round behavior used by the runtime balancer.

concepts: dict[str, list[list[str]]] = {element: [line.split('|') for line in (ROOT / 'data' / 'card_sets' / f'{element}_concepts.tsv').read_text().splitlines()] for element in TYPES}  # Loads authored concepts rather than assembling random names or anatomy.
assert all(len(rows) == 80 and all(len(row) == 4 for row in rows) for rows in concepts.values())  # Requires complete consistently shaped source lists.
cards: list[Card] = []  # Collects the unfinished interleaved set before difficulty classification.
for index in range(80):  # Spreads each element across the entire numbered set.
    for element_index, element in enumerate(TYPES):  # Adds one creature of each element per numbering block.
        name, subject, first_move, second_move = concepts[element][index]  # Retains the authored identity and attacks.
        number: str = str(len(cards) + 1).zfill(4)  # Maintains sequential species identifiers.
        health, speed = PROFILES[(index + element_index * 3) % len(PROFILES)]  # Rotates the same underlying combat archetypes within every type.
        prompt: str = f'{STYLE}\n\nSUBJECT: {name}, an original standalone {element}-type monster. Depict {subject}. Present this single complete creature in a clear three-quarter view, with its face and defining anatomical features legible. Keep the entire silhouette comfortably inside the portrait with an even paper margin. Preserve coherent anatomy, consistent limb proportions, believable joints and a unified perspective. Render each described material with its own watercolor surface character, using {PALETTES[element]} as the supporting palette while retaining the specified colors. Use a calm expressive pose suited to its body, carefully separated appendages and a soft grounded contact shadow directly beneath it. Focus all detail on the creature, with generous clean off-white paper surrounding the silhouette.'  # Makes every stored prompt usable independently by the image generator.
        cards.append(Card(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f'card_foundry/standalone_400/{number}')), species_id=number, species_name=name, type=element, difficulty='easy', is_final_boss=False, art='', art_prompt=prompt, art_width=1122, art_height=1402, art_zoom=1, art_x=50, art_y=50, health=health, speed=speed, moves=[Move(name=first_move, mana_cost=1, damage=20), Move(name=second_move, mana_cost=2, damage=40)], revision=1))  # Assembles the editable seed while preserving its original health-versus-speed profile.
for element in TYPES:  # Classifies each element independently to preserve an even elemental mix at every difficulty.
    ranked: list[Card] = sorted((card for card in cards if card['type'] == element), key=lambda card: (threat_score(card), card['species_id']))  # Orders gentle concepts first and threatening concepts last.
    assert len(ranked) == 80  # Requires exactly eighty cards before quintile assignment.
    for rank, card in enumerate(ranked):  # Walks the ordered concepts from easiest to strongest.
        card['difficulty'] = DIFFICULTIES[min(len(DIFFICULTIES) - 1, rank // 16)]  # Assigns exactly sixteen monsters of this element to each band.
for card in cards:  # Applies difficulty-specific statistics after every concept has a band.
    if card['species_id'] == '0400':  # Elevates the final card beyond the ordinary Ultra envelope.
        card['difficulty'] = 'ultra'  # Keeps the final boss inside the highest named group.
        card['is_final_boss'] = True  # Marks the unique climactic encounter explicitly.
        card['art_prompt'] = f'{STYLE}\n\n{FINAL_BOSS_SUBJECT}'  # Replaces the modest original concept with a monumental final-boss design.
        card['health'] = 540  # Gives the boss substantially more durability than a normal Ultra monster.
        card['speed'] = 160  # Keeps the boss fast enough to feel climactic despite its large body.
        card['moves'] = [Move(name='voidwhisker rend', mana_cost=4, damage=180), Move(name='last eclipse', mana_cost=7, damage=360)]  # Gives the boss two unique attacks beyond the normal Ultra damage ceiling.
        continue  # Skips the standard band scaling for the special boss record.
    original_total: int = max(1, card['health'] + card['speed'])  # Protects the original archetype ratio from division by zero.
    health_ratio: float = card['health'] / original_total  # Captures how tank-oriented the authored profile is.
    target_total: int = STAT_TOTALS[card['difficulty']]  # Selects the combined power budget for the assigned tier.
    health: int = max(20, min(target_total - 20, round_to_five(target_total * health_ratio)))  # Scales durability while retaining a usable speed floor.
    card['health'] = health  # Stores the tier-adjusted durability.
    card['speed'] = target_total - health  # Preserves the exact combined tier budget after rounding.
    first_band, second_band = MOVE_BANDS[card['difficulty']]  # Selects the two attack profiles for this difficulty.
    card['moves'] = [Move(name=card['moves'][0]['name'], mana_cost=first_band[0], damage=first_band[1]), Move(name=card['moves'][1]['name'], mana_cost=second_band[0], damage=second_band[1])]  # Preserves authored move names while applying progression combat values.
assert len(cards) == 400 and Counter(card['type'] for card in cards) == Counter({element: 80 for element in TYPES})  # Enforces the requested total and equal element distribution.
assert Counter(card['difficulty'] for card in cards) == Counter({difficulty: 80 for difficulty in DIFFICULTIES})  # Enforces exactly eighty monsters in every named difficulty.
assert all(sum(1 for card in cards if card['type'] == element and card['difficulty'] == difficulty) == 16 for element in TYPES for difficulty in DIFFICULTIES)  # Enforces sixteen monsters of every element inside every difficulty.
assert len({card['species_name'] for card in cards}) == len(cards)  # Rejects repeated species names.
assert len({move['name'] for card in cards for move in card['moves']}) == len(cards) * 2  # Rejects repeated attack names including the final boss attacks.
assert sum(1 for card in cards if card['is_final_boss']) == 1 and cards[-1]['species_id'] == '0400' and cards[-1]['is_final_boss'] and cards[-1]['difficulty'] == 'ultra'  # Guarantees Duskervet is the sole final boss in the last card slot.
assert all(card['art'] == '' and len(card['art_prompt']) <= 6000 for card in cards)  # Keeps every art slot empty and prompts inside the editor limit.
(ROOT / 'data' / 'standalone_400.json').write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n')  # Saves reproducible difficulty-aware source data for the durable collection installer.
print(f"validated {len(cards)} cards; 80 per difficulty; 16 of each type per difficulty; final boss {cards[-1]['species_name']} at #0400")  # Reports the progression invariants after generation.
