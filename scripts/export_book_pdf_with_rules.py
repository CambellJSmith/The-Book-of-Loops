from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import export_book_pdf as base
import export_book_pdf_dense as dense
import export_book_pdf_with_lore as lore
import gameplay_rules as game

PAGE_WIDTH, PAGE_HEIGHT = A4
RULES_PAGE = 2
LOCATION_PAGE_START = 3
MONSTER_PAGE_START = 103
TOTAL_PAGES = 122
FINAL_LOCATION_NAME = "Stillwater sanctum"


def starting_villages(
    locations: list[dict[str, Any]],
    adjacency: dict[str, list[str]],
    page_by_id: dict[str, int],
) -> list[tuple[int, str, int]]:
    starts: list[tuple[int, str, int]] = []
    for location in locations:
        location_id = str(location.get("id", ""))
        name = str(location.get("name", location_id))
        if name == FINAL_LOCATION_NAME or len(adjacency.get(location_id, [])) != 1:
            continue
        starts.append((len(starts) + 1, name, page_by_id[location_id]))
    if len(starts) != 6:
        raise RuntimeError(f"expected 6 starting villages, found {len(starts)}")
    return starts


def draw_rule_panel(
    pdf: canvas.Canvas,
    number: str,
    title: str,
    body: str,
    x: float,
    top: float,
    width: float,
    height: float,
    body_size: float = 9.0,
) -> None:
    accent = colors.HexColor("#d8b36a")
    y = top - height
    pdf.setFillColor(base.PANEL)
    pdf.setStrokeColor(base.BORDER)
    pdf.setLineWidth(0.8)
    pdf.roundRect(x, y, width, height, 7, fill=1, stroke=1)

    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 8)
    pdf.drawString(x + 12, top - 20, number)
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 12)
    pdf.drawString(x + 35, top - 22, title)

    item = base.paragraph(body, body_size, base.MUTED, leading=body_size * 1.35)
    _, body_height = item.wrap(width - 24, height - 46)
    item.drawOn(pdf, x + 12, top - 39 - body_height)


def draw_rules_page(pdf: canvas.Canvas, starts: list[tuple[int, str, int]]) -> None:
    base.draw_page_background(pdf)
    bookmark = "gameplay_rules"
    pdf.bookmarkPage(bookmark)
    pdf.addOutlineEntry("Gameplay Rules", bookmark, level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 8.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 47, "THE BOOK OF LOOPS")
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 26)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 80, "Gameplay Rules")
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 9)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 99, "All random results use one six-sided die (d6).")
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.4)
    pdf.line(PAGE_WIDTH / 2 - 70, PAGE_HEIGHT - 111, PAGE_WIDTH / 2 + 70, PAGE_HEIGHT - 111)

    x = base.MARGIN
    width = PAGE_WIDTH - 2 * base.MARGIN
    table_top = PAGE_HEIGHT - 137
    table_height = 111
    pdf.setFillColor(base.PANEL)
    pdf.setStrokeColor(base.BORDER)
    pdf.roundRect(x, table_top - table_height, width, table_height, 7, fill=1, stroke=1)
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 11)
    pdf.drawString(x + 12, table_top - 21, "1. Roll for your starting village")
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 8.4)
    pdf.drawString(x + 12, table_top - 38, "Roll once, then go directly to the matching village page.")

    column_width = (width - 36) / 3
    row_y = table_top - 63
    for index, (roll, name, page_number) in enumerate(starts):
        column = index % 3
        row = index // 3
        cell_x = x + 12 + column * (column_width + 6)
        cell_y = row_y - row * 28
        pdf.setFillColor(accent)
        pdf.setFont(base.FONT_BOLD, 8.5)
        pdf.drawString(cell_x, cell_y, str(roll))
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_BOLD, 8.3)
        pdf.drawString(cell_x + 14, cell_y, name)
        pdf.setFillColor(base.SOFT)
        pdf.setFont(base.FONT_REGULAR, 7.5)
        pdf.drawRightString(cell_x + column_width, cell_y, f"p. {page_number}")

    panel_top = table_top - table_height - 12
    gap = 10
    left_width = (width - gap) / 2
    right_x = x + left_width + gap

    draw_rule_panel(
        pdf,
        "2",
        "Choose your starter",
        "At your starting village, roll the d6 again and read that village's monster encounter table. The monster shown for your roll becomes your starter at full health. You do not battle this first monster. Once you have your starter, choose one of the listed travel routes and move to that location.",
        x,
        panel_top,
        left_width,
        132,
    )
    draw_rule_panel(
        pdf,
        "3",
        "Find an encounter",
        "Whenever you arrive at a new location, roll the d6 and use that location's monster encounter table. The result is the monster you must battle. After the battle is resolved, use the travel choices on the location page to decide where to go next.",
        right_x,
        panel_top,
        left_width,
        132,
    )

    second_top = panel_top - 144
    draw_rule_panel(
        pdf,
        "4",
        "Battle order",
        "Compare the Speed of your monster with the enemy monster. The monster with the higher Speed acts first each round. If the Speeds are tied, roll the d6 for each monster; the higher roll acts first, rerolling further ties.",
        x,
        second_top,
        left_width,
        112,
    )
    draw_rule_panel(
        pdf,
        "5",
        "Moves and Mana",
        f"Each monster starts a battle with {game.STARTING_MANA} Mana and gains {game.MANA_PER_TURN} Mana at the start of its turn. Mana carries between turns, is spent to use moves, and resets after battle. A monster can use only moves it can afford. You choose your monster's move. For an enemy, roll d6: 1-3 selects Move 1; 4-6 selects Move 2. If that move is unaffordable, use the other if affordable. If neither is affordable, it does not attack and keeps its Mana. Move 2 always costs more Mana and deals more damage than Move 1.",
        right_x,
        second_top,
        left_width,
        170,
        body_size=8.2,
    )

    third_top = second_top - 182
    draw_rule_panel(
        pdf,
        "6",
        "Defeat and death",
        "When a monster's Health reaches 0, it dies immediately. If it belongs to the player, permanently discard that monster from the team. A defeated monster does not take any remaining turn that round.",
        x,
        third_top,
        left_width,
        124,
    )
    draw_rule_panel(
        pdf,
        "7",
        "Recruit a defeated monster",
        f"When an enemy monster reaches 0 Health, roll the d6 once. On a 5-6, it can join your team at full Health. You can carry a maximum of {game.TEAM_SIZE_LIMIT} monsters. If you already have {game.TEAM_SIZE_LIMIT} when recruitment succeeds, choose one monster to discard: either the new monster or one you are already carrying. There is no storage or reserve team. On a 1-4, the monster is not recruited.",
        right_x,
        third_top,
        left_width,
        124,
        body_size=7.8,
    )

    note_y = third_top - 140
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 9)
    pdf.drawCentredString(PAGE_WIDTH / 2, note_y, "Travel. Battle. Recruit. Keep moving through the loop.")

    base.draw_footer(pdf, RULES_PAGE, "Gameplay Rules")
    pdf.showPage()


def export_pdf(output_path: Path) -> None:
    base.register_fonts()
    map_data = json.loads(base.MAP_PATH.read_text(encoding="utf-8"))
    card_data = json.loads(base.CARD_PATH.read_text(encoding="utf-8"))
    encounter_data = json.loads(dense.ENCOUNTER_PATH.read_text(encoding="utf-8"))
    locations = list(map_data.get("locations", []))
    source_cards = sorted(list(card_data.get("cards", [])), key=lambda card: str(card.get("species_id", "")))
    if len(locations) != 100:
        raise RuntimeError(f"expected 100 locations, found {len(locations)}")
    if len(source_cards) != 400:
        raise RuntimeError(f"expected 400 monsters, found {len(source_cards)}")
    invalid_move_order = [str(card.get("species_id", "")) for card in source_cards if not game.move_two_is_stronger(card)]
    if invalid_move_order:
        raise RuntimeError(f"move 2 must cost more mana and deal more damage than move 1 for every monster: {invalid_move_order[:8]}")

    encounter_metadata = dense.build_encounter_metadata(encounter_data)
    if len(encounter_metadata) != 400:
        raise RuntimeError(f"expected encounter metadata for 400 monsters, found {len(encounter_metadata)}")

    cards: list[dict[str, Any]] = []
    for source_card in source_cards:
        species_id = str(source_card.get("species_id", ""))
        metadata = encounter_metadata.get(species_id)
        if metadata is None:
            raise RuntimeError(f"missing encounter metadata for species {species_id}")
        card = dict(source_card)
        card.update(metadata)
        cards.append(card)

    location_by_id = {str(location.get("id")): location for location in locations}
    page_by_id = {str(location.get("id")): index + LOCATION_PAGE_START for index, location in enumerate(locations)}
    adjacency = base.build_adjacency(map_data)
    starts = starting_villages(locations, adjacency, page_by_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("Opening lore, gameplay rules, 100-location adventure map, and dense 400-monster reference")

    lore.draw_lore_page(pdf)
    draw_rules_page(pdf, starts)

    art_count = 0
    for index, location in enumerate(locations):
        page_number = LOCATION_PAGE_START + index
        if lore.draw_location_page(pdf, location, page_number, index + 1, location_by_id, page_by_id, adjacency):
            art_count += 1

    for group_index in range(0, len(cards), dense.MONSTERS_PER_PAGE):
        page_number = MONSTER_PAGE_START + group_index // dense.MONSTERS_PER_PAGE
        dense.draw_monster_reference_page(pdf, cards[group_index : group_index + dense.MONSTERS_PER_PAGE], page_number)

    pdf.save()
    print(f"wrote {output_path}")
    print(
        f"pages={TOTAL_PAGES} lore_pages=1 rules_pages=1 locations=100 monsters=400 "
        f"monsters_per_page={dense.MONSTERS_PER_PAGE} location_art_present={art_count} "
        f"location_art_missing={100 - art_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export The Book of Loops with lore, gameplay rules, locations, and monster reference.")
    parser.add_argument("--output", default="book_of_loops.pdf")
    args = parser.parse_args()
    export_pdf(Path(args.output))


if __name__ == "__main__":
    main()
