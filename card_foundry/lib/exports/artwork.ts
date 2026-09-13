export interface EmbeddedArtwork { mime_type: string; encoding: "base64"; data: string; } // stores portable raster bytes without a private site URL.

export function blob_data_url(blob: Blob): Promise<string> { // encodes image bytes for independent SVG and JSON files.
  return new Promise((resolve, reject) => { // waits for the complete file conversion.
    const reader: FileReader = new FileReader(); // converts binary artwork to a data URL.
    reader.onload = (): void => resolve(String(reader.result)); // returns the encoded artwork.
    reader.onerror = (): void => reject(new Error("could not read the artwork")); // preserves the export failure for the caller.
    reader.readAsDataURL(blob); // starts the binary conversion.
  });
}
export async function fetch_artwork(source: string): Promise<Blob> { // retrieves artwork that must travel with the exported card.
  if (!/^(\/sample_art\.webp|\/api\/art\/[a-f0-9-]{36})$/.test(source)) throw new Error("choose artwork uploaded to this editor before exporting"); // keeps artwork reads within the current studio.
  const response: Response = await fetch(source); // fetches the actual stored artwork bytes.
  if (!response.ok) throw new Error("artwork could not be loaded; please try again"); // prevents silently incomplete exports.
  const blob: Blob = await response.blob(); // retains the image's verified content type.
  if (!["image/png", "image/jpeg", "image/webp"].includes(blob.type) || !blob.size || blob.size > 8 * 1024 * 1024) throw new Error("the artwork response was not a supported image"); // rejects sign-in pages and unsupported payloads.
  return blob; // supplies valid self-contained image bytes.
}
export async function embed_artwork(source: string): Promise<EmbeddedArtwork> { // makes an image portable across programs and computers.
  const blob: Blob = await fetch_artwork(source); // retrieves the checked raster image.
  const encoded: string = await blob_data_url(blob); // converts the image bytes to base64.
  return { mime_type: blob.type, encoding: "base64", data: encoded.slice(encoded.indexOf(",") + 1) }; // stores only the binary encoding after the data-URL prefix.
}
export async function svg_artwork_url(source: string, compatible: boolean): Promise<string> { // embeds artwork in an SVG without an online dependency.
  const blob: Blob = await fetch_artwork(source); // loads the same artwork used by the preview.
  if (!compatible || blob.type !== "image/webp") return blob_data_url(blob); // retains widely supported raster formats and fast browser rendering.
  const image: ImageBitmap = await createImageBitmap(blob); // decodes WebP for editors with limited SVG image support.
  try { // releases decoded artwork even if conversion fails.
    const canvas: HTMLCanvasElement = document.createElement("canvas"); // creates a lossless compatibility image.
    canvas.width = image.width; canvas.height = image.height; // preserves the original artwork dimensions.
    const context: CanvasRenderingContext2D | null = canvas.getContext("2d"); // obtains the raster conversion surface.
    if (!context) throw new Error("artwork conversion is unavailable in this browser"); // reports unavailable image conversion.
    context.drawImage(image, 0, 0); // preserves artwork proportions and transparency.
    const png: Blob = await new Promise((resolve, reject) => canvas.toBlob((result: Blob | null): void => result ? resolve(result) : reject(new Error("could not embed the artwork")), "image/png")); // converts WebP into a widely supported embedded raster.
    return await blob_data_url(png); // returns the portable PNG image reference.
  } finally { image.close(); } // releases decoded image memory.
}
