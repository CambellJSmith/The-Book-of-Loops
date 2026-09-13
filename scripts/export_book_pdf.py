from __future__ import annotations

import argparse
import json
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "location_map.json"
CARD_PATH = ROOT / "card_foundry" / "data" / "card_objects.json"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 36
BACKGROUND = colors.HexColor("#111419")
PANEL = colors.HexColor("#1c2128")
PANEL_2 = colors.HexColor("#242b34")
BORDER = colors.HexColor("#39414d")
TEXT = colors.HexColor("#f4f0e8")
MUTED = colors.HexColor("#a8b0bc")
SOFT = colors.HexColor("#77808d")
ELEMENT_COLORS = {
    "fire": colors.HexColor("#f29255"),
    "water": colors.HexColor("#60bff5"),
    "nature": colors.HexColor("#91c974"),
    "light": colors.HexColor("#ead58a"),
    "dark": colors.HexColor("#b49bea"),
}

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
_IMAGE_CACHE: dict[Path, ImageReader] = {}


def register_fonts() -> None:
    global FONT_REGULAR, FONT_BOLD
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("BookSans", str(regular)))
        pdfmetrics.registerFont(TTFont("BookSansBold", str(bold)))
        FONT_REGULAR = "BookSans"
        FONT_BOLD = "BookSansBold"


def draw_page_background(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(BACKGROUND)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)


def draw_footer(pdf: canvas.Canvas, page_number: int, label: str) -> None:
    pdf.setStrokeColor(colors.HexColor("#2a3039"))
    pdf.setLineWidth(0.6)
    pdf.line(MARGIN, 23, PAGE_WIDTH - MARGIN, 23)
    pdf.setFillColor(SOFT)
    pdf.setFont(FONT_REGULAR, 7.5)
    pdf.drawString(MARGIN, 11, label)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 11, f"page {page_number}")


def paragraph(text: str, size: float, color: colors.Color = MUTED, leading: float | None = None) -> Paragraph:
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    style = ParagraphStyle(
        "body",
        fontName=FONT_REGULAR,
        fontSize=size,
        leading=leading or size * 1.28,
        textColor=color,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
    )
    return Paragraph(safe, style)


def fit_paragraph(text: str, width: float, max_height: float, preferred: float = 10) -> tuple[Paragraph, float, float]:
    for size in (preferred, preferred - 0.5, preferred - 1.0, preferred - 1.5, preferred - 2.0, 7.0):
        item = paragraph(text, max(7.0, size))
        _, height = item.wrap(width, max_height * 4)
        if height <= max_height:
            return item, width, height
    item = paragraph(text, 7.0, leading=8.3)
    _, height = item.wrap(width, max_height * 4)
    return item, width, height


def load_image(path: Path) -> ImageReader | None:
    if not path.exists():
        return None
    cached = _IMAGE_CACHE.get(path)
    if cached is not None:
        return cached
    try:
        with PILImage.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((1600, 1600), PILImage.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=86, optimize=True)
            buffer.seek(0)
            reader = ImageReader(buffer)
            _IMAGE_CACHE[path] = reader
            return reader
    except Exception:
        return None


def draw_contained_image(pdf: canvas.Canvas, reader: ImageReader, x: float, y: float, width: float, height: float) -> None:
    img_width, img_height = reader.getSize()
    scale = min(width / img_width, height / img_height)
    draw_width = img_width * scale
    draw_height = img_height * scale
    draw_x = x + (width - draw_width) / 2
    draw_y = y + (height - draw_height) / 2
    pdf.drawImage(reader, draw_x, draw_y, draw_width, draw_height, preserveAspectRatio=True, mask="auto")


def build_adjacency(map_data: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for link in map_data.get("links", []):
        source = str(link.get("source", ""))
        target = str(link.get("target", ""))
        if source and target:
            result[source].add(target)
            result[target].add(source)
    return {key: sorted(values) for key, values in result.items()}


def draw_location_page(
    pdf: canvas.Canvas,
    location: dict[str, Any],
    page_number: int,
    location_by_id: dict[str, dict[str, Any]],
    page_by_id: dict[str, int],
    adjacency: dict[str, list[str]],
) -> bool:
    draw_page_background(pdf)
    location_id = str(location.get("id", ""))
    name = str(location.get("name", location_id))
    description = str(location.get("description", "")).strip() or "No description is currently stored for this location."
    pdf.bookmarkPage(location_id)
    pdf.addOutlineEntry(f"{page_number:03d} - {name}", location_id, level=0, closed=False)

    accent = colors.HexColor("#d8b36a")
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, 22)
    title = name
    max_title_width = PAGE_WIDTH - 2 * MARGIN - 85
    title_size = 22
    while title_size > 14 and pdfmetrics.stringWidth(title, FONT_BOLD, title_size) > max_title_width:
        title_size -= 1
    pdf.setFont(FONT_BOLD, title_size)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 54, title)
    pdf.setFillColor(accent)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 50, f"LOCATION {page_number:03d} / 100")
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(2)
    pdf.line(MARGIN, PAGE_HEIGHT - 66, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 66)

    desc_top = PAGE_HEIGHT - 84
    desc_width = PAGE_WIDTH - 2 * MARGIN
    desc_item, _, desc_height = fit_paragraph(description, desc_width, 105, preferred=9.5)
    desc_item.drawOn(pdf, MARGIN, desc_top - desc_height)

    art_top = desc_top - desc_height - 14
    art_height = max(235, min(310, art_top - 430))
    art_bottom = art_top - art_height
    pdf.setFillColor(PANEL)
    pdf.setStrokeColor(BORDER)
    pdf.setLineWidth(1)
    pdf.roundRect(MARGIN, art_bottom, desc_width, art_height, 8, fill=1, stroke=1)

    art_path = ROOT / f"{name}.png"
    reader = load_image(art_path)
    has_art = reader is not None
    if reader is not None:
        inset = 7
        draw_contained_image(pdf, reader, MARGIN + inset, art_bottom + inset, desc_width - inset * 2, art_height - inset * 2)
    else:
        pdf.setFillColor(colors.HexColor("#8993a1"))
        pdf.setFont(FONT_BOLD, 26)
        pdf.drawCentredString(PAGE_WIDTH / 2, art_bottom + art_height / 2 + 7, "no_art")
        pdf.setFillColor(SOFT)
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawCentredString(PAGE_WIDTH / 2, art_bottom + art_height / 2 - 13, f"expected file: {name}.png")

    table_top = art_bottom - 18
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(MARGIN, table_top, "monster_encounters - roll d6")
    row_top = table_top - 10
    row_height = 20
    col_x = [MARGIN, MARGIN + 38, MARGIN + 92, MARGIN + 310, MARGIN + 400]
    headers = ["d6", "id", "monster", "type", "difficulty"]
    pdf.setFillColor(colors.HexColor("#20262e"))
    pdf.rect(MARGIN, row_top - row_height, desc_width, row_height, fill=1, stroke=0)
    pdf.setFillColor(MUTED)
    pdf.setFont(FONT_BOLD, 7.5)
    for x, header in zip(col_x, headers):
        pdf.drawString(x + 5, row_top - 13, header)

    encounters = list(location.get("encounters", []))[:6]
    for index in range(6):
        y = row_top - (index + 2) * row_height
        entry = encounters[index] if index < len(encounters) else {}
        if index % 2 == 0:
            pdf.setFillColor(colors.HexColor("#181d23"))
            pdf.rect(MARGIN, y, desc_width, row_height, fill=1, stroke=0)
        roll = str(entry.get("roll", index + 1))
        species_id = str(entry.get("species_id", "----"))
        species_name = str(entry.get("species_name", "unassigned"))
        element = str(entry.get("type", ""))
        difficulty = str(entry.get("difficulty", "")).replace("_", " ")
        pdf.setFont(FONT_BOLD, 8.5)
        pdf.setFillColor(ELEMENT_COLORS.get(element, TEXT))
        pdf.drawString(col_x[0] + 7, y + 6, roll)
        pdf.setFillColor(TEXT)
        pdf.setFont(FONT_REGULAR, 8)
        pdf.drawString(col_x[1] + 5, y + 6, f"#{species_id}")
        name_size = 8
        while name_size > 6 and pdfmetrics.stringWidth(species_name, FONT_BOLD, name_size) > 205:
            name_size -= 0.5
        pdf.setFont(FONT_BOLD, name_size)
        pdf.drawString(col_x[2] + 5, y + 6, species_name)
        pdf.setFont(FONT_REGULAR, 8)
        pdf.setFillColor(ELEMENT_COLORS.get(element, MUTED))
        pdf.drawString(col_x[3] + 5, y + 6, element)
        pdf.setFillColor(MUTED)
        pdf.drawString(col_x[4] + 5, y + 6, difficulty)

    exits_y = row_top - 7 * row_height - 18
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(MARGIN, exits_y, "travel")
    exits_y -= 18
    neighbors = adjacency.get(location_id, [])
    for neighbor_id in neighbors:
        target = location_by_id.get(neighbor_id, {})
        target_name = str(target.get("name", neighbor_id))
        target_page = page_by_id.get(neighbor_id)
        if target_page is None:
            continue
        line = f"To go to {target_name}, go to page {target_page}."
        pdf.setFillColor(MUTED)
        pdf.setFont(FONT_REGULAR, 9)
        pdf.drawString(MARGIN + 10, exits_y, line)
        text_width = pdfmetrics.stringWidth(line, FONT_REGULAR, 9)
        pdf.linkRect("", neighbor_id, (MARGIN + 8, exits_y - 3, MARGIN + 12 + text_width, exits_y + 10), relative=0, thickness=0)
        exits_y -= 15

    draw_footer(pdf, page_number, f"{location_id} - {name}")
    pdf.showPage()
    return has_art


def draw_card_shape(pdf: canvas.Canvas, card: dict[str, Any], x: float, y: float, width: float, height: float) -> None:
    accent = ELEMENT_COLORS.get(str(card.get("type", "dark")), ELEMENT_COLORS["dark"])
    sx = width / 750.0
    sy = height / 1050.0

    def X(value: float) -> float:
        return x + value * sx

    def Y(value: float) -> float:
        return y + value * sy

    pdf.saveState()
    pdf.setFillColor(colors.HexColor("#14171c"))
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(max(0.7, 5 * sx))
    pdf.roundRect(x, y, width, height, 10 * sx, fill=1, stroke=1)

    art_x = X(28)
    art_y = Y(412)
    art_w = 694 * sx
    art_h = 610 * sy
    pdf.setFillColor(PANEL_2)
    pdf.rect(art_x, art_y, art_w, art_h, fill=1, stroke=0)

    art = card.get("art")
    art_drawn = False
    if isinstance(art, str) and art:
        candidate = ROOT / art.lstrip("/")
        reader = load_image(candidate)
        if reader is not None:
            draw_contained_image(pdf, reader, art_x, art_y, art_w, art_h)
            art_drawn = True
    if not art_drawn:
        pdf.setFillColor(colors.HexColor("#8993a1"))
        pdf.setFont(FONT_BOLD, max(7, 20 * sx))
        pdf.drawCentredString(x + width / 2, Y(700), "add your artwork")

    species_id = str(card.get("species_id", "0000"))
    species_name = str(card.get("species_name", "your monster"))
    element = str(card.get("type", "dark"))
    id_box_w = max(118 * sx, min(230 * sx, (len(species_id) + 1) * 15 * sx + 30 * sx))
    pdf.setFillColor(colors.HexColor("#161a20"))
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(max(0.4, sx))
    pdf.rect(X(48), Y(950), id_box_w, 52 * sy, fill=1, stroke=1)
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_REGULAR, max(6.5, 18 * sx))
    pdf.drawString(X(64), Y(969), f"#{species_id}")

    badge_w = 148 * sx
    badge_h = 46 * sy
    pdf.setFillColor(accent)
    pdf.rect(X(545), Y(942), badge_w, badge_h, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#191b20"))
    pdf.setFont(FONT_BOLD, max(6.2, 16 * sx))
    pdf.drawCentredString(X(619), Y(958), element)

    pdf.setFillColor(accent)
    pdf.rect(X(48), Y(468), 44 * sx, max(1.2, 4 * sy), fill=1, stroke=0)
    name_size = 42 * sx
    max_name_width = 640 * sx
    while name_size > 11 and pdfmetrics.stringWidth(species_name, FONT_BOLD, name_size) > max_name_width:
        name_size -= 0.7
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, name_size)
    pdf.drawString(X(48), Y(432), species_name)

    stat_y = Y(284)
    stat_h = 92 * sy
    pdf.setFillColor(colors.HexColor("#24282e"))
    pdf.rect(X(48), stat_y, 654 * sx, stat_h, fill=1, stroke=0)
    pdf.setStrokeColor(accent)
    pdf.setLineWidth(max(0.5, 2.5 * sy))
    pdf.line(X(48), stat_y + stat_h, X(702), stat_y + stat_h)
    pdf.setFillColor(MUTED)
    pdf.setFont(FONT_REGULAR, max(5.5, 13 * sx))
    pdf.drawString(X(77), Y(327), "health")
    pdf.drawString(X(408), Y(327), "speed")
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, max(8, 28 * sx))
    pdf.drawRightString(X(348), Y(312), str(card.get("health", 0)))
    pdf.drawRightString(X(679), Y(312), str(card.get("speed", 0)))

    moves = list(card.get("moves", []))[:2]
    for index in range(2):
        move = moves[index] if index < len(moves) else {}
        base = 170 - index * 103
        center_x = X(84)
        center_y = Y(base + 21)
        radius = 26 * sx
        pdf.setFillColor(colors.Color(accent.red, accent.green, accent.blue, alpha=0.13))
        pdf.setStrokeColor(accent)
        pdf.circle(center_x, center_y, radius, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.setFont(FONT_BOLD, max(7, 18 * sx))
        pdf.drawCentredString(center_x, center_y - 6 * sy, str(move.get("mana_cost", 0)))
        move_name = str(move.get("name", f"move {index + 1}"))
        move_size = 19 * sx
        while move_size > 7 and pdfmetrics.stringWidth(move_name, FONT_BOLD, move_size) > 360 * sx:
            move_size -= 0.5
        pdf.setFillColor(TEXT)
        pdf.setFont(FONT_BOLD, move_size)
        pdf.drawString(X(143), Y(base + 27), move_name)
        pdf.setFillColor(MUTED)
        pdf.setFont(FONT_REGULAR, max(5.2, 11.5 * sx))
        pdf.drawString(X(143), Y(base + 1), f"{move.get('mana_cost', 0)} mana")
        pdf.setFillColor(TEXT)
        pdf.setFont(FONT_BOLD, max(7.5, 24 * sx))
        pdf.drawRightString(X(696), Y(base + 25), str(move.get("damage", 0)))
        pdf.setFillColor(MUTED)
        pdf.setFont(FONT_REGULAR, max(5.2, 10.5 * sx))
        pdf.drawRightString(X(696), Y(base + 2), "damage")
        if index == 0:
            pdf.setStrokeColor(colors.HexColor("#383d44"))
            pdf.setLineWidth(max(0.35, sx))
            pdf.line(X(48), Y(122), X(702), Y(122))

    pdf.restoreState()


def draw_card_page(pdf: canvas.Canvas, cards: list[dict[str, Any]], page_number: int, first_index: int) -> None:
    draw_page_background(pdf)
    first_id = str(cards[0].get("species_id", "")) if cards else ""
    last_id = str(cards[-1].get("species_id", "")) if cards else ""
    bookmark = f"cards_{first_id}"
    pdf.bookmarkPage(bookmark)
    pdf.addOutlineEntry(f"cards {first_id}-{last_id}", bookmark, level=0, closed=False)
    pdf.setFillColor(TEXT)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 27, f"monster_cards - #{first_id} to #{last_id}")
    pdf.setFillColor(SOFT)
    pdf.setFont(FONT_REGULAR, 7.5)
    pdf.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 27, "4 cards per page - species id order")

    gap_x = 16
    gap_y = 16
    usable_width = PAGE_WIDTH - 2 * MARGIN
    top = PAGE_HEIGHT - 42
    bottom = 30
    usable_height = top - bottom
    card_width = (usable_width - gap_x) / 2
    card_height = min(card_width * 1.4, (usable_height - gap_y) / 2)
    card_width = card_height / 1.4
    total_width = card_width * 2 + gap_x
    start_x = (PAGE_WIDTH - total_width) / 2
    start_y = bottom + usable_height - card_height

    positions = [
        (start_x, start_y),
        (start_x + card_width + gap_x, start_y),
        (start_x, start_y - card_height - gap_y),
        (start_x + card_width + gap_x, start_y - card_height - gap_y),
    ]
    for card, (x, y) in zip(cards, positions):
        draw_card_shape(pdf, card, x, y, card_width, card_height)

    draw_footer(pdf, page_number, f"monster cards {first_index + 1:04d}-{first_index + len(cards):04d}")
    pdf.showPage()


def export_pdf(output_path: Path) -> None:
    register_fonts()
    map_data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    card_data = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    locations = list(map_data.get("locations", []))
    cards = sorted(list(card_data.get("cards", [])), key=lambda card: str(card.get("species_id", "")))
    if len(locations) != 100:
        raise RuntimeError(f"expected 100 locations, found {len(locations)}")
    if len(cards) != 400:
        raise RuntimeError(f"expected 400 monster cards, found {len(cards)}")

    location_by_id = {str(location.get("id")): location for location in locations}
    page_by_id = {str(location.get("id")): index + 1 for index, location in enumerate(locations)}
    adjacency = build_adjacency(map_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("The Book of Loops")
    pdf.setAuthor("The Book of Loops")
    pdf.setSubject("100-location adventure map and 400 monster cards")

    art_count = 0
    for index, location in enumerate(locations):
        if draw_location_page(pdf, location, index + 1, location_by_id, page_by_id, adjacency):
            art_count += 1

    card_page_start = 101
    for group_index in range(0, len(cards), 4):
        page_number = card_page_start + group_index // 4
        draw_card_page(pdf, cards[group_index : group_index + 4], page_number, group_index)

    pdf.save()
    print(f"wrote {output_path}")
    print(f"pages=200 locations=100 cards=400 location_art_present={art_count} location_art_missing={100 - art_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export The Book of Loops as a print-ready PDF.")
    parser.add_argument("--output", default="book_of_loops.pdf")
    args = parser.parse_args()
    export_pdf(Path(args.output))


if __name__ == "__main__":
    main()
