import type { MonsterCard } from "./card_model"; // shares the complete card snapshot used by the preview.
import { create_card_svg } from "./exports/card_svg"; // keeps raster and vector exports on the same exact layout.
import { card_filename, download_blob } from "./exports/download"; // shares safe filenames and browser download handling.

export async function export_card_png(svg: SVGSVGElement, card: MonsterCard): Promise<void> { // exports exactly the card shown in the editor.
  const source: string = await create_card_svg(svg, card); // embeds the current artwork into the shared vector layout.
  const url: string = URL.createObjectURL(new Blob([source], { type: "image/svg+xml;charset=utf-8" })); // provides a temporary render source.
  try { // releases temporary resources on every outcome.
    const rendered: HTMLImageElement = new Image(); // renders the vector card.
    await new Promise<void>((resolve, reject) => { // waits for the image to decode.
      rendered.onload = (): void => resolve(); // continues once ready.
      rendered.onerror = (): void => reject(new Error("could not render this card")); // reports render failures.
      rendered.src = url; // begins the SVG render.
    });
    const canvas: HTMLCanvasElement = document.createElement("canvas"); // creates the raster surface.
    canvas.width = 1500; canvas.height = 2100; // matches the exported vector dimensions.
    const context: CanvasRenderingContext2D | null = canvas.getContext("2d"); // obtains the drawing context.
    if (!context) throw new Error("image export is unavailable in this browser"); // handles missing canvas support.
    context.drawImage(rendered, 0, 0); // draws the exact visible layout.
    const png: Blob = await new Promise((resolve, reject) => canvas.toBlob((blob: Blob | null): void => blob ? resolve(blob) : reject(new Error("could not create the png")), "image/png")); // encodes the finished card.
    download_blob(png, card_filename(card, "png")); // downloads the card using the shared file lifecycle.
  } finally { URL.revokeObjectURL(url); } // releases the vector source.
}
