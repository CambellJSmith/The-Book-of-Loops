from collections import Counter  # Checks uniqueness and equal type counts.
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
STYLE: str = ('STYLE: 1122 × 1402 px portrait artwork; roughly 4:5 portrait aspect ratio; museum-quality traditional watercolor illustration on cold-pressed cotton paper; layered transparent washes; luminous glazing; controlled wet-on-wet transitions; fine dry-brush texture; natural pigment granulation; crisp value-defined edges; subtle watercolor blooms; carefully modeled volume; rich harmonious color; refined storybook concept-art finish; soft grounded contact shadow; generous clean off-white paper field; centered single-creature presentation; high-resolution scan quality.')  # Keeps the shared visual treatment independent of creature anatomy.
PALETTES: dict[str, str] = {'fire': 'ember orange, copper, brick red and warm charcoal', 'water': 'deep teal, cerulean, frosted blue and pearl', 'nature': 'moss green, warm bark brown, fresh leaf green and botanical accent colors', 'light': 'warm ivory, pale gold, opal and luminous pastel highlights', 'dark': 'charcoal, deep indigo, muted violet and restrained silver highlights'}  # Harmonizes each element without changing the authored materials.
PROFILES: tuple[tuple[int, int], ...] = ((80, 100), (90, 90), (100, 80), (110, 70), (120, 60), (130, 50), (140, 40), (150, 30), (160, 20), (115, 65))  # Gives every element an identical distribution of durability and initiative.
concepts: dict[str, list[list[str]]] = {element: [line.split('|') for line in (ROOT / 'data' / 'card_sets' / f'{element}_concepts.tsv').read_text().splitlines()] for element in TYPES}  # Loads authored concepts rather than assembling random names or anatomy.
assert all(len(rows) == 80 and all(len(row) == 4 for row in rows) for rows in concepts.values())  # Requires complete consistently shaped source lists.
cards: list[Card] = []  # Collects the finished interleaved set.
for index in range(80):  # Spreads each element across the entire numbered set.
    for element_index, element in enumerate(TYPES):  # Adds one creature of each element per numbering block.
        name, subject, first_move, second_move = concepts[element][index]  # Retains the authored identity and attacks.
        number: str = str(len(cards) + 1).zfill(4)  # Maintains sequential species identifiers.
        health, speed = PROFILES[(index + element_index * 3) % len(PROFILES)]  # Rotates the same stat profiles independently within each type.
        first_cost: int = 1 + (index // 10) % 2  # Distributes inexpensive attack choices evenly.
        second_cost: int = 3 + (index // 20) % 2  # Distributes stronger attack choices evenly.
        prompt: str = f'{STYLE}\n\nSUBJECT: {name}, an original standalone {element}-type monster. Depict {subject}. Present this single complete creature in a clear three-quarter view, with its face and defining anatomical features legible. Keep the entire silhouette comfortably inside the portrait with an even paper margin. Preserve coherent anatomy, consistent limb proportions, believable joints and a unified perspective. Render each described material with its own watercolor surface character, using {PALETTES[element]} as the supporting palette while retaining the specified colors. Use a calm expressive pose suited to its body, carefully separated appendages and a soft grounded contact shadow directly beneath it. Focus all detail on the creature, with generous clean off-white paper surrounding the silhouette.'  # Makes every stored prompt usable independently by the image generator.
        cards.append(Card(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f'card_foundry/standalone_400/{number}')), species_id=number, species_name=name, type=element, art='', art_prompt=prompt, art_width=1122, art_height=1402, art_zoom=1, art_x=50, art_y=50, health=health, speed=speed, moves=[Move(name=first_move, mana_cost=first_cost, damage=first_cost * 20), Move(name=second_move, mana_cost=second_cost, damage=second_cost * 20)], revision=1))  # Assembles the complete editable card while leaving its artwork empty.
assert len(cards) == 400 and Counter(card['type'] for card in cards) == Counter({element: 80 for element in TYPES})  # Enforces the requested total and equal distribution.
assert len({card['species_name'] for card in cards}) == len(cards)  # Rejects repeated species names.
assert len({move['name'] for card in cards for move in card['moves']}) == len(cards) * 2  # Rejects repeated attack names.
assert all(card['art'] == '' and len(card['art_prompt']) <= 6000 for card in cards)  # Keeps every art slot empty and prompts inside the editor limit.
(ROOT / 'data' / 'standalone_400.json').write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n')  # Saves reproducible source data for the durable collection installer.
print(f'validated {len(cards)} cards; {len(cards) * 2} unique moves; 80 per type; all art empty')  # Reports the meaningful completion checks.
