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

PAGE_WIDTH, PAGE_HEIGHT = A4
MONSTERS_PER_PAGE = 20
MONSTER_COLUMNS = 2
MONSTER_ROWS = 10


def fit_text_size(text: str, font_name: str, preferred: float, minimum: float, max_width: float) -> float:
    size = preferred
    while size > minimum and pdfmetrics.stringWidth(text, font_name, size) > max_width:
        size -= 0.25
    return max(minimum, size)


def draw_monster_entry(pdf: canvas.Canvas, card: dict[str, Any], x: float, y: float, width: float, height: float) -> None:
    element = str(card.get("type", "dark"))
    accent = base.ELEMENT_COLORS.get(element, base.ELEMENT_COLORS["dark"])
    species_id = str(card.get("species_id", "0000"))
    species_name = str(card.get("species_name", "unnamed"))
    difficulty = str(card.get("difficulty", "easy")).replace("_", " ")
    health = str(card.get("health", 0))
    speed = str(card.get("speed", 0))
    is_final_boss = bool(card.get("is_final_boss", False))
    moves = list(card.get("moves", []))[:2]

    pdf.setFillColor(base.PANEL)
    pdf.setStrokeColor(base.BORDER)
    pdf.setLineWidth(0.55)
    pdf.roundRect(x, y, width, height, 4, fill=1, stroke=1)
    pdf.setFillColor(accent)
    pdf.rect(x, y + height - 3, width, 3, fill=1, stroke=0)

    pad = 7
    top = y + height - 14
    id_text = f"#{species_id}"
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 7.5)
    pdf.drawString(x + pad, top, id_text)

    name_x = x + pad + 36
    name_width = width - (name_x - x) - pad - 58
    name_size = fit_text_size(species_name, base.FONT_BOLD, 9.2, 6.8, name_width)
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, name_size)
    pdf.drawString(name_x, top, species_name)

    badge = "FINAL BOSS" if is_final_boss else difficulty.upper()
    badge_size = fit_text_size(badge, base.FONT_BOLD, 6.2, 5.2, 54)
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, badge_size)
    pdf.drawRightString(x + width - pad, top, badge)

    meta_y = top - 13
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 6.8)
    pdf.drawString(x + pad, meta_y, "type")
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 6.8)
    pdf.drawString(x + pad + 25, meta_y, element)
    pdf.setFillColor(base.MUTED)
    pdf.setFont(base.FONT_REGULAR, 6.8)
    pdf.drawString(x + pad + 76, meta_y, f"HP {health}")
    pdf.drawString(x + pad + 122, meta_y, f"SPD {speed}")

    move_start = meta_y - 14
    for index in range(2):
        move = moves[index] if index < len(moves) else {}
        move_name = str(move.get("name", f"move {index + 1}"))
        mana = str(move.get("mana_cost", 0))
        damage = str(move.get("damage", 0))
        line_y = move_start - index * 14

        pdf.setFillColor(accent)
        pdf.setFont(base.FONT_BOLD, 6.8)
        pdf.drawString(x + pad, line_y, f"{mana}M")

        damage_text = f"{damage} dmg"
        damage_width = pdfmetrics.stringWidth(damage_text, base.FONT_BOLD, 6.8)
        right_edge = x + width - pad
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_BOLD, 6.8)
        pdf.drawRightString(right_edge, line_y, damage_text)

        move_x = x + pad + 25
        move_width = right_edge - damage_width - 9 - move_x
        move_size = fit_text_size(move_name, base.FONT_REGULAR, 6.8, 5.5, move_width)
        pdf.setFillColor(base.TEXT)
        pdf.setFont(base.FONT_REGULAR, move_size)
        pdf.drawString(move_x, line_y, move_name)


def draw_monster_reference_page(pdf: canvas.Canvas, cards: list[dict[str, Any]], page_number: int) -> None:
    base.draw_page_background(pdf)
    first_id = str(cards[0].get("species_id", "")) if cards else ""
    last_id = str(cards[-1].get("species_id", "")) if cards else ""
    bookmark = f"monsters_{first_id}"
    pdf.bookmarkPage(bookmark)
    pdf.addOutlineEntry(f"monsters {first_id}-{last_id}", bookmark, level=0, closed=False)

    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, 13)
    pdf.drawString(base.MARGIN, PAGE_HEIGHT - 29, f"monster_reference - #{first_id} to #{last_id}")
    pdf.setFillColor(base.SOFT)
    pdf.setFont(base.FONT_REGULAR, 7.5)
    pdf.drawRightString(PAGE_WIDTH - base.MARGIN, PAGE_HEIGHT - 29, "20 monsters per page - species id order")

    gap_x = 10
    gap_y = 5
    usable_width = PAGE_WIDTH - 2 * base.MARGIN
    top = PAGE_HEIGHT - 43
    bottom = 31
    usable_height = top - bottom
    column_width = (usable_width - gap_x) / MONSTER_COLUMNS
    entry_height = (usable_height - gap_y * (MONSTER_ROWS - 1)) / MONSTER_ROWS

    for index, card in enumerate(cards):
        row = index // MONSTER_COLUMNS
        column = index % MONSTER_COLUMNS
        x = base.MARGIN + column * (column_width + gap_x)
        y = top - (row + 1) * entry_height - row * gap_y
        draw_monster_entry(pdf, card, x, y, column_width, entry_height)

    base.draw_footer(pdf, page_number, f"monster reference #{first_id}-#{last_id}")
    pdf.showPage()


def export_pdf(output_path: Path) -> None:
    base.register_fonts()
    map_data = json.loads(base.MAP_PATH.read_text(encoding="utf-8"))
    card_data = json.loads(base.CARD_PATH.read_text(encoding="utf-8"))
    locations = list(map_data.get("locations", []))
    cards = sorted(list(card_data.get("cards", [])), key=lambda card: str(card.get("species_id", "")))
    if len(locations) != 100:
        raise RuntimeError(f"expected 100 locations, found {len(locations)}")
    if len(cards) != 400:
        raise RuntimeError(f"expected 400 monsters, found {len(cards)}")

    location_by_id = {str(location.get("id")): location for location in locations}
    page_by_id = {str(location.get("id")): index + 1 for index, location in enumerate(locations)}
    adjacency = base.build_adjacency(map_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("100-location adventure map and dense 400-monster reference")

    art_count = 0
    for index, location in enumerate(locations):
        if base.draw_location_page(pdf, location, index + 1, location_by_id, page_by_id, adjacency):
            art_count += 1

    monster_page_start = 101
    for group_index in range(0, len(cards), MONSTERS_PER_PAGE):
        page_number = monster_page_start + group_index // MONSTERS_PER_PAGE
        draw_monster_reference_page(pdf, cards[group_index : group_index + MONSTERS_PER_PAGE], page_number)

    pdf.save()
    total_pages = 100 + (len(cards) + MONSTERS_PER_PAGE - 1) // MONSTERS_PER_PAGE
    print(f"wrote {output_path}")
    print(
        f"pages={total_pages} locations=100 monsters=400 monsters_per_page={MONSTERS_PER_PAGE} "
        f"location_art_present={art_count} location_art_missing={100 - art_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export The Book of Loops with a dense monster reference appendix.")
    parser.add_argument("--output", default="book_of_loops.pdf")
    args = parser.parse_args()
    export_pdf(Path(args.output))


if __name__ == "__main__":
    main()
