from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

import export_book_pdf as base
import export_book_pdf_dense as dense
import healing_locations as healing

PAGE_WIDTH, PAGE_HEIGHT = A4
LOCATION_PAGE_START = 2
MONSTER_PAGE_START = 102
TOTAL_PAGES = 121

STORY_PARAGRAPHS = [
    "There was a time before the turning.",
    "The rivers kept their courses. The orchards flowered when they were meant to, and the roads carried merchants, pilgrims, children, and old friends from one end of the land to the other. Villages grew without fear of vanishing by morning. Seasons passed. People aged. Things began, and things ended.",
    "Above all of it, unseen by most and worshipped by few, Duskervet kept watch.",
    "He was not a king, nor a god in any sense the people understood. He was simply there, as constant as the stars and as distant as the horizon, guardian of the passage from one moment into the next. Time moved because it was allowed to move, and Duskervet made certain that nothing reached into its current and bent it out of shape.",
    "For an age beyond counting, there was no need for anyone to know his name.",
    "Then someone came for him.",
    "No record tells who struck first, or why. No witness agrees on what happened in the Stillwater Sanctum that night. Some stories speak of a blade. Others of a machine, a spell, a voice from somewhere beyond the world. Whatever the truth, Duskervet was wounded, and in that single terrible instant he saw something coming that he could not permit to happen.",
    "So he stopped it.",
    "Not forever.",
    "Just long enough.",
    "He reached across the whole of the land and folded time back upon itself. Rivers returned to their banks. Broken doors stood whole again. Blood vanished from stone. The dead breathed. The sun rose once more over the same morning.",
    "And when the danger came again, the world turned again.",
    "And again.",
    "And again.",
    "The people do not remember. Not properly. A dream here. A familiar face where none should be. A road taken for the first time that somehow feels well travelled. The world wakes each cycle believing itself new.",
    "But time remembers.",
    "The land has begun to change beneath the strain of repetition. Roads meet where they once could not. Creatures appear far from where they began. Places seem to lean toward one another across impossible distances. There are ruins with no history, songs no one remembers learning, and warnings carved into stone by hands whose owners have never held a chisel.",
    "At the centre of it all, Duskervet still watches.",
    "Whether he is protecting the world, imprisoning it, or simply waiting for something to change is no longer known.",
    "Only this remains certain:",
    "the loop has been running for a very long time.",
    "And this time, you remember.",
]


def draw_story_column(pdf: canvas.Canvas, paragraphs: list[str], x: float, top: float, width: float) -> None:
    y = top
    for index, text in enumerate(paragraphs):
        is_short_emphasis = len(text) < 45
        size = 10.2 if is_short_emphasis else 9.2
        colour = base.TEXT if is_short_emphasis else base.MUTED
        item = base.paragraph(text, size, colour, leading=size * 1.34)
        _, height = item.wrap(width, PAGE_HEIGHT)
        y -= height
        item.drawOn(pdf, x, y)
        y -= 10 if is_short_emphasis else 8


def draw_lore_page(pdf: canvas.Canvas) -> None:
    base.draw_page_background(pdf)
    bookmark = "the_first_loop"
    pdf.bookmarkPage(bookmark)
    pdf.addOutlineEntry("The First Loop", bookmark, level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 8.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 48, "THE BOOK OF LOOPS")

    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 27)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 82, "The First Loop")

    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.4)
    pdf.line(PAGE_WIDTH / 2 - 70, PAGE_HEIGHT - 96, PAGE_WIDTH / 2 + 70, PAGE_HEIGHT - 96)

    column_gap = 24
    usable_width = PAGE_WIDTH - 2 * base.MARGIN
    column_width = (usable_width - column_gap) / 2
    column_top = PAGE_HEIGHT - 122
    left = STORY_PARAGRAPHS[:11]
    right = STORY_PARAGRAPHS[11:]
    draw_story_column(pdf, left, base.MARGIN, column_top, column_width)
    draw_story_column(pdf, right, base.MARGIN + column_width + column_gap, column_top, column_width)

    base.draw_footer(pdf, 1, "The First Loop")
    pdf.showPage()


def draw_location_page(
    pdf: canvas.Canvas,
    location: dict[str, Any],
    page_number: int,
    location_number: int,
    location_by_id: dict[str, dict[str, Any]],
    page_by_id: dict[str, int],
    adjacency: dict[str, list[str]],
) -> bool:
    base.draw_page_background(pdf)
    location_id = str(location.get("id", ""))
    name = str(location.get("name", location_id))
    description = str(location.get("description", "")).strip() or "No description is currently stored for this location."
    pdf.bookmarkPage(location_id)
    pdf.addOutlineEntry(f"{location_number:03d} - {name}", location_id, level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(base.TEXT)
    title = name
    max_title_width = PAGE_WIDTH - 2 * base.MARGIN - 85
    title_size = 22
    while title_size > 14 and pdfmetrics.stringWidth(title, base.FONT_BOLD, title_size) > max_title_width:
        title_size -= 1
    pdf.setFont(base.FONT_BOLD, title_size)
    pdf.drawString(base.MARGIN, PAGE_HEIGHT - 54, title)
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 9)
    pdf.drawRightString(PAGE_WIDTH - base.MARGIN, PAGE_HEIGHT - 50, f"LOCATION {location_number:03d} / 100")
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(2)
    pdf.line(base.MARGIN, PAGE_HEIGHT - 66, PAGE_WIDTH - base.MARGIN, PAGE_HEIGHT - 66)

    desc_top = PAGE_HEIGHT - 84
    desc_width = PAGE_WIDTH - 2 * base.MARGIN
    desc_item, _, desc_height = base.fit_paragraph(description, desc_width, 105, preferred=9.5)
    desc_item.drawOn(pdf, base.MARGIN, desc_top - desc_height)

    art_top = desc_top - desc_height - 14
    art_height = max(235, min(310, art_top - 430))
    art_bottom = art_top - art_height
    pdf.setFillColor(base.PANEL)
    pdf.setStrokeColor(base.BORDER)
    pdf.setLineWidth(1)
    pdf.roundRect(base.MARGIN, art_bottom, desc_width, art_height, 8, fill=1, stroke=1)

    art_path = base.ROOT / f"{name}.png"
    reader = base.load_image(art_path)
    has_art = reader is not None
    if reader is not None:
        inset = 7
        base.draw_contained_image(pdf, reader, base.MARGIN + inset, art_bottom + inset, desc_width - inset * 2, art_height - inset * 2)
    else:
        pdf.setFillColor(colors.HexColor("#8993a1"))
        pdf.setFont(base.FONT_BOLD, 26)
        pdf.drawCentredString(PAGE_WIDTH / 2, art_bottom + art_height / 2 + 7, "no_art")
        pdf.setFillColor(base.SOFT)
        pdf.setFont(base.FONT_REGULAR, 8)
        pdf.drawCentredString(PAGE_WIDTH / 2, art_bottom + art_height / 2 - 13, f"expected file: {name}.png")

    table_top = art_bottom - 18
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 10)
    pdf.drawString(base.MARGIN, table_top, "monster_encounters - roll d6")
    row_top = table_top - 10
    row_height = 20
    col_x = [base.MARGIN, base.MARGIN + 38, base.MARGIN + 92, base.MARGIN + 390]
    headers = ["d6", "id", "monster", "type"]
    pdf.setFillColor(colors.HexColor("#20262e"))
    pdf.rect(base.MARGIN, row_top - row_height, desc_width, row_height, fill=1, stroke=0)
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_BOLD, 7.5)
    for x, header in zip(col_x, headers):
        pdf.drawString(x + 5, row_top - 13, header)

    encounters = list(location.get("encounters", []))[:6]
    for index in range(6):
        y = row_top - (index + 2) * row_height
        entry = encounters[index] if index < len(encounters) else {}
        if index % 2 == 0:
            pdf.setFillColor(colors.HexColor("#181d23"))
            pdf.rect(base.MARGIN, y, desc_width, row_height, fill=1, stroke=0)
        roll = str(entry.get("roll", index + 1))
        species_id = str(entry.get("species_id", "----"))
        species_name = str(entry.get("species_name", "unassigned"))
        element = str(entry.get("type", ""))
        pdf.setFont(base.FONT_BOLD, 8.5)
        pdf.setFillColor(base.ELEMENT_COLORS.get(element, base.TEXT))
        pdf.drawString(col_x[0] + 7, y + 6, roll)
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_REGULAR, 8)
        pdf.drawString(col_x[1] + 5, y + 6, f"#{species_id}")
        name_size = 8
        while name_size > 6 and pdfmetrics.stringWidth(species_name, base.FONT_BOLD, name_size) > 285:
            name_size -= 0.5
        pdf.setFont(base.FONT_BOLD, name_size)
        pdf.drawString(col_x[2] + 5, y + 6, species_name)
        pdf.setFont(base.FONT_REGULAR, 8)
        pdf.setFillColor(base.ELEMENT_COLORS.get(element, base.MUTED))
        pdf.drawString(col_x[3] + 5, y + 6, element)

    exits_y = row_top - 7 * row_height - 18
    if location_id in healing.HEALING_LOCATION_IDS:
        panel_height = 45
        panel_bottom = exits_y - panel_height
        pdf.setFillColor(base.PANEL)
        pdf.setStrokeColor(base.BORDER)
        pdf.setLineWidth(0.8)
        pdf.roundRect(base.MARGIN, panel_bottom, desc_width, panel_height, 7, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.setFont(base.FONT_BOLD, 8)
        pdf.drawString(base.MARGIN + 12, exits_y - 16, "HEALING")
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_REGULAR, 9)
        pdf.drawString(base.MARGIN + 12, exits_y - 32, healing.HEALING_NOTE)
        exits_y = panel_bottom - 16

    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 10)
    pdf.drawString(base.MARGIN, exits_y, "travel")
    exits_y -= 18
    for neighbor_id in adjacency.get(location_id, []):
        target = location_by_id.get(neighbor_id, {})
        target_name = str(target.get("name", neighbor_id))
        target_page = page_by_id.get(neighbor_id)
        if target_page is None:
            continue
        line = f"To go to {target_name}, go to page {target_page}."
        pdf.setFillColor(base.MUTED)
        pdf.setFont(base.FONT_REGULAR, 9)
        pdf.drawString(base.MARGIN + 10, exits_y, line)
        text_width = pdfmetrics.stringWidth(line, base.FONT_REGULAR, 9)
        pdf.linkRect("", neighbor_id, (base.MARGIN + 8, exits_y - 3, base.MARGIN + 12 + text_width, exits_y + 10), relative=0, thickness=0)
        exits_y -= 15

    base.draw_footer(pdf, page_number, f"{location_id} - {name}")
    pdf.showPage()
    return has_art


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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("Opening lore, 100-location adventure map, and dense 400-monster reference")

    draw_lore_page(pdf)

    art_count = 0
    for index, location in enumerate(locations):
        page_number = LOCATION_PAGE_START + index
        if draw_location_page(pdf, location, page_number, index + 1, location_by_id, page_by_id, adjacency):
            art_count += 1

    for group_index in range(0, len(cards), dense.MONSTERS_PER_PAGE):
        page_number = MONSTER_PAGE_START + group_index // dense.MONSTERS_PER_PAGE
        dense.draw_monster_reference_page(pdf, cards[group_index : group_index + dense.MONSTERS_PER_PAGE], page_number)

    pdf.save()
    print(f"wrote {output_path}")
    print(
        f"pages={TOTAL_PAGES} lore_pages=1 locations=100 monsters=400 monsters_per_page={dense.MONSTERS_PER_PAGE} "
        f"location_art_present={art_count} location_art_missing={100 - art_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export The Book of Loops with opening lore, locations, and dense monster reference.")
    parser.add_argument("--output", default="book_of_loops.pdf")
    args = parser.parse_args()
    export_pdf(Path(args.output))


if __name__ == "__main__":
    main()
