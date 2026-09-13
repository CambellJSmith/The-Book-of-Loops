import { card_schema, type MonsterCard } from "@/lib/card_model"; // validates the visual card's underlying data.
import { svg_artwork_url } from "./artwork"; // embeds portable artwork instead of online image references.
import { card_filename, download_blob } from "./download"; // shares safe filenames and browser download behavior.

export async function create_card_svg(svg: SVGSVGElement, card: MonsterCard, compatible_artwork: boolean = false): Promise<string> { // serializes the visible card as editable SVG objects.
  const parsed: MonsterCard = card_schema.parse(card); // prevents incomplete cards from becoming finished exports.
  const copy: SVGSVGElement = svg.cloneNode(true) as SVGSVGElement; // isolates export preparation from the live preview.
  copy.setAttribute("width", "1500"); copy.setAttribute("height", "2100"); // preserves the established export dimensions and proportions.
  copy.removeAttribute("class"); // removes application-only styles from the standalone file.
  if (compatible_artwork) copy.setAttributeNS("http://www.w3.org/2000/xmlns/", "xmlns:xlink", "http://www.w3.org/1999/xlink"); // supports image references in established SVG editors.
  copy.setAttribute("aria-label", `${parsed.species_name}, ${parsed.type}, health ${parsed.health}, speed ${parsed.speed}`); // retains an accessible description with the independent file.
  for (const image of Array.from(copy.querySelectorAll("image"))) { // embeds every artwork object in the layout.
    const source: string | null = image.getAttribute("href"); // reads the source used by the preview.
    if (!source) continue; // skips empty artwork references.
    const encoded: string = await svg_artwork_url(source, compatible_artwork); // converts unsupported embedded formats when exporting editable SVG.
    if (compatible_artwork) { image.removeAttribute("href"); image.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", encoded); } // uses one embedded payload compatible with established SVG importers.
    else image.setAttribute("href", encoded); // keeps the browser's PNG render on its existing image-link format.
  }
  return new XMLSerializer().serializeToString(copy); // retains text, groups, paths, gradients, and clipping as code-based objects.
}
export async function export_card_svg(svg: SVGSVGElement, card: MonsterCard): Promise<void> { // exports an editable visual card for other design programs.
  const source: string = await create_card_svg(svg, card, true); // embeds compatible artwork while preserving vector objects.
  download_blob(new Blob([`<?xml version="1.0" encoding="UTF-8"?>\n`, source], { type: "image/svg+xml;charset=utf-8" }), card_filename(card, "svg")); // downloads the complete self-contained SVG document.
}
