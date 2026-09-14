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
import export_book_pdf_with_lore as lore
import export_book_pdf_with_rules as rules
import gameplay_rules as game

PAGE_WIDTH, PAGE_HEIGHT = A4
COVER_PAGE = 1
CONTENTS_PAGE = 2
LORE_PAGE = 3
RULES_PAGE = 4
LOCATION_PAGE_START = 5
MONSTER_PAGE_START = 105
TOTAL_PAGES = 124


def draw_loop_mark(pdf: canvas.Canvas, centre_x: float, centre_y: float) -> None:
    accent = colors.HexColor("#d8b36a")
    pdf.saveState()
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.3)
    for angle, width, height in ((-38, 150, 47), (0, 168, 52), (38, 150, 47)):
        pdf.saveState()
        pdf.translate(centre_x, centre_y)
        pdf.rotate(angle)
        pdf.ellipse(-width / 2, -height / 2, width / 2, height / 2, fill=0, stroke=1)
        pdf.restoreState()
    pdf.setFillColor(accent)
    pdf.circle(centre_x, centre_y, 3.4, fill=1, stroke=0)
    pdf.restoreState()


def draw_cover_page(pdf: canvas.Canvas) -> None:
    base.draw_page_background(pdf)
    pdf.bookmarkPage("cover")
    pdf.addOutlineEntry("Cover", "cover", level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 8.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 72, "A DICE-DRIVEN MONSTER ADVENTURE")

    draw_loop_mark(pdf, PAGE_WIDTH / 2, PAGE_HEIGHT - 220)

    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 43)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 355, "THE BOOK")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 52)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 414, "OF LOOPS")

    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.5)
    pdf.line(PAGE_WIDTH / 2 - 92, PAGE_HEIGHT - 442, PAGE_WIDTH / 2 + 92, PAGE_HEIGHT - 442)

    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 11)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 476, "Travel. Battle. Recruit. Keep moving through the loop.")

    pdf.setFillColor(base.SOFT)
    pdf.setFont(base.FONT_REGULAR, 8.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, 76, "A world caught in time, waiting for something to change.")
    pdf.showPage()


def contents_link_row(
    pdf: canvas.Canvas,
    label: str,
    page_text: str,
    destination: str,
    y: float,
    x: float,
    width: float,
    size: float = 11,
) -> None:
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, size)
    pdf.drawString(x, y, label)
    page_width = pdfmetrics.stringWidth(page_text, base.FONT_BOLD, size)
    label_width = pdfmetrics.stringWidth(label, base.FONT_BOLD, size)
    dots_left = x + label_width + 8
    dots_right = x + width - page_width - 12
    if dots_right > dots_left:
        pdf.setFillColor(base.SOFT)
        pdf.setFont(base.FONT_REGULAR, size - 1.5)
        dot_width = max(2.0, pdfmetrics.stringWidth(".", base.FONT_REGULAR, size - 1.5))
        dot_count = max(1, int((dots_right - dots_left) / dot_width))
        pdf.drawString(dots_left, y, "." * dot_count)
    pdf.setFillColor(colors.HexColor("#d8b36a"))
    pdf.setFont(base.FONT_BOLD, size)
    pdf.drawRightString(x + width, y, page_text)
    pdf.linkRect("", destination, (x - 2, y - 5, x + width + 2, y + size + 4), relative=0, thickness=0)


def draw_contents_page(
    pdf: canvas.Canvas,
    starts: list[tuple[int, str, str, int]],
    first_location_id: str,
) -> None:
    base.draw_page_background(pdf)
    pdf.bookmarkPage("contents")
    pdf.addOutlineEntry("Contents", "contents", level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 8.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 48, "THE BOOK OF LOOPS")
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 28)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 84, "Contents")
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(1.4)
    pdf.line(PAGE_WIDTH / 2 - 70, PAGE_HEIGHT - 99, PAGE_WIDTH / 2 + 70, PAGE_HEIGHT - 99)

    x = base.MARGIN + 18
    width = PAGE_WIDTH - 2 * x
    y = PAGE_HEIGHT - 145

    pdf.setFillColor(base.SOFT)
    pdf.setFont(base.FONT_BOLD, 7.5)
    pdf.drawString(x, y, "FRONT MATTER")
    y -= 28
    contents_link_row(pdf, "The First Loop", str(LORE_PAGE), "the_first_loop", y, x, width)
    y -= 30
    contents_link_row(pdf, "Gameplay Rules", str(RULES_PAGE), "gameplay_rules", y, x, width)

    y -= 48
    pdf.setFillColor(base.SOFT)
    pdf.setFont(base.FONT_BOLD, 7.5)
    pdf.drawString(x, y, "THE WORLD")
    y -= 28
    contents_link_row(pdf, "Locations 001-100", f"{LOCATION_PAGE_START}-{LOCATION_PAGE_START + 99}", first_location_id, y, x, width)

    y -= 42
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 8.8)
    pdf.drawString(x, y, "Starting villages")
    y -= 24
    village_gap = 23
    for roll, location_id, name, page_number in starts:
        pdf.setFillColor(accent)
        pdf.setFont(base.FONT_BOLD, 8.2)
        pdf.drawString(x + 8, y, str(roll))
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_BOLD, 9.3)
        pdf.drawString(x + 29, y, name)
        pdf.setFillColor(accent)
        pdf.setFont(base.FONT_BOLD, 8.8)
        pdf.drawRightString(x + width, y, str(page_number))
        pdf.linkRect("", location_id, (x + 4, y - 5, x + width + 2, y + 12), relative=0, thickness=0)
        y -= village_gap

    y -= 23
    pdf.setFillColor(base.SOFT)
    pdf.setFont(base.FONT_BOLD, 7.5)
    pdf.drawString(x, y, "MONSTER REFERENCE")
    y -= 28
    contents_link_row(pdf, "Species #0001-#0400", f"{MONSTER_PAGE_START}-{TOTAL_PAGES}", "monsters_0001", y, x, width)

    y -= 55
    pdf.setFillColor(base.PANEL)
    pdf.setStrokeColor(base.BORDER)
    pdf.setLineWidth(0.8)
    note_height = 62
    pdf.roundRect(x, y - note_height, width, note_height, 7, fill=1, stroke=1)
    note = base.paragraph(
        "In the digital PDF, contents entries, travel instructions, locations and monster-reference sections are clickable for quick navigation.",
        8.8,
        base.MUTED,
        leading=12,
    )
    _, note_text_height = note.wrap(width - 24, note_height - 18)
    note.drawOn(pdf, x + 12, y - 13 - note_text_height)

    base.draw_footer(pdf, CONTENTS_PAGE, "Contents")
    pdf.showPage()


def starting_villages(
    locations: list[dict[str, Any]],
    adjacency: dict[str, list[str]],
    page_by_id: dict[str, int],
) -> list[tuple[int, str, str, int]]:
    starts: list[tuple[int, str, str, int]] = []
    for location in locations:
        location_id = str(location.get("id", ""))
        name = str(location.get("name", location_id))
        if name == rules.FINAL_LOCATION_NAME or len(adjacency.get(location_id, [])) != 1:
            continue
        starts.append((len(starts) + 1, location_id, name, page_by_id[location_id]))
    if len(starts) != 6:
        raise RuntimeError(f"expected 6 starting villages, found {len(starts)}")
    return starts


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
    first_location_id = str(locations[0].get("id", ""))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("Cover, contents, opening lore, gameplay rules, 100-location adventure map, and dense 400-monster reference")

    draw_cover_page(pdf)
    draw_contents_page(pdf, starts, first_location_id)
    lore.draw_lore_page(pdf, page_number=LORE_PAGE)

    rules.RULES_PAGE = RULES_PAGE
    rules.draw_rules_page(pdf, [(roll, name, page_number) for roll, _location_id, name, page_number in starts])

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
        f"pages={TOTAL_PAGES} cover_pages=1 contents_pages=1 lore_pages=1 rules_pages=1 "
        f"locations=100 monsters=400 monsters_per_page={dense.MONSTERS_PER_PAGE} "
        f"location_art_present={art_count} location_art_missing={100 - art_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the complete Book of Loops with cover, contents, lore, rules, locations, and monster reference.")
    parser.add_argument("--output", default="book_of_loops.pdf")
    args = parser.parse_args()
    export_pdf(Path(args.output))


if __name__ == "__main__":
    main()
