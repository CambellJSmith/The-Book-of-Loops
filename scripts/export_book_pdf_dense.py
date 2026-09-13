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
ENCOUNTER_PATH = base.ROOT / "monster_encounters.json"


def fit_text_size(text: str, font_name: str, preferred: float, minimum: float, max_width: float) -> float:
    size = preferred
    while size > minimum and pdfmetrics.stringWidth(text, font_name, size) > max_width:
        size -= 0.25
    return max(minimum, size)


def build_encounter_metadata(encounter_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    final_boss_id = str(encounter_data.get("rules", {}).get("final_boss", {}).get("species_id", "0400"))
    for location in encounter_data.get("locations", []):
        for monster in location.get("unique_monsters", []):
            species_id = str(monster.get("species_id", ""))
            if not species_id:
                continue
            metadata[species_id] = {
                "is_final_boss": bool(monster.get("is_final_boss", False)) or species_id == final_boss_id,
            }
    return metadata


def draw_location_page(
    pdf: canvas.Canvas,
    location: dict[str, Any],
    page_number: int,
    location_by_id: dict[str, dict[str, Any]],
    page_by_id: dict[str, int],
    adjacency: dict[str, list[str]],
) -> bool:
    base.draw_page_background(pdf)
    location_id = str(location.get("id", ""))
    name = str(location.get("name", location_id))
    description = str(location.get("description", "")).strip() or "No description is currently stored for this location."
    pdf.bookmarkPage(location_id)
    pdf.addOutlineEntry(f"{page_number:03d} - {name}", location_id, level=0, closed=False)

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
    pdf.drawRightString(PAGE_WIDTH - base.MARGIN, PAGE_HEIGHT - 50, f"LOCATION {page_number:03d} / 100")
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


def draw_monster_entry(pdf: canvas.Canvas, card: dict[str, Any], x: float, y: float, width: float, height: float) -> None:
    element = str(card.get("type", "dark"))
    accent = base.ELEMENT_COLORS.get(element, base.ELEMENT_COLORS["dark"])
    species_id = str(card.get("species_id", "0000"))
    species_name = str(card.get("species_name", "unnamed"))
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
    pdf.setFillColor(accent)
    pdf.setFont(base.FONT_BOLD, 7.5)
    pdf.drawString(x + pad, top, f"#{species_id}")

    name_x = x + pad + 36
    reserved_right = 58 if is_final_boss else 0
    name_width = width - (name_x - x) - pad - reserved_right
    name_size = fit_text_size(species_name, base.FONT_BOLD, 9.2, 6.8, name_width)
    pdf.setFillColor(base.TEXT)
    pdf.setFont(base.FONT_BOLD, name_size)
    pdf.drawString(name_x, top, species_name)

    if is_final_boss:
        badge = "FINAL BOSS"
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
    encounter_data = json.loads(ENCOUNTER_PATH.read_text(encoding="utf-8"))
    locations = list(map_data.get("locations", []))
    source_cards = sorted(list(card_data.get("cards", [])), key=lambda card: str(card.get("species_id", "")))
    if len(locations) != 100:
        raise RuntimeError(f"expected 100 locations, found {len(locations)}")
    if len(source_cards) != 400:
        raise RuntimeError(f"expected 400 monsters, found {len(source_cards)}")

    encounter_metadata = build_encounter_metadata(encounter_data)
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
    page_by_id = {str(location.get("id")): index + 1 for index, location in enumerate(locations)}
    adjacency = base.build_adjacency(map_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("100-location adventure map and dense 400-monster reference")

    art_count = 0
    for index, location in enumerate(locations):
        if draw_location_page(pdf, location, index + 1, location_by_id, page_by_id, adjacency):
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
