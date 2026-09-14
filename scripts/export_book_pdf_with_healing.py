from __future__ import annotations

import json
from typing import Any

import export_book_pdf as base
import export_book_pdf_complete as complete
import export_book_pdf_with_lore as lore
import gameplay_rules as game

_original_draw_location_page = lore.draw_location_page


def draw_location_page_with_healing(
    pdf,
    location: dict[str, Any],
    page_number: int,
    location_number: int,
    location_by_id: dict[str, dict[str, Any]],
    page_by_id: dict[str, int],
    adjacency: dict[str, list[str]],
) -> bool:
    rendered_location = location
    if location.get("healing_location"):
        rendered_location = dict(location)
        description = str(location.get("description", "")).strip()
        healing_section = f"<b>healing</b><br/>{game.HEALING_NOTE}"
        rendered_location["description"] = f"{description}<br/><br/>{healing_section}" if description else healing_section
    return _original_draw_location_page(
        pdf,
        rendered_location,
        page_number,
        location_number,
        location_by_id,
        page_by_id,
        adjacency,
    )


def validate_healing_map() -> None:
    map_data = json.loads(base.MAP_PATH.read_text(encoding="utf-8"))
    healing_locations = [location for location in map_data.get("locations", []) if location.get("healing_location")]
    if len(healing_locations) != game.HEALING_LOCATION_COUNT:
        raise RuntimeError(f"expected {game.HEALING_LOCATION_COUNT} healing locations, found {len(healing_locations)}")
    forbidden = {f"loc_{index:03d}" for index in range(1, 7)} | {"loc_100"}
    invalid = [str(location.get("id", "")) for location in healing_locations if str(location.get("id", "")) in forbidden]
    if invalid:
        raise RuntimeError(f"starting villages and Stillwater sanctum cannot be healing locations: {invalid}")


def main() -> None:
    validate_healing_map()
    lore.draw_location_page = draw_location_page_with_healing
    complete.main()


if __name__ == "__main__":
    main()
