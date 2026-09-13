export interface PreparedArt { blob: Blob; width: number; height: number; } // carries normalized image bytes and their dimensions.

export async function prepare_art(file: File): Promise<PreparedArt> { // checks and scales uploaded artwork before saving it.
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) throw new Error("choose a png, jpg, or webp image"); // accepts only supported raster formats.
  if (file.size > 20 * 1024 * 1024) throw new Error("choose an image smaller than 20 mb"); // avoids oversized input files.
  const image: ImageBitmap = await createImageBitmap(file); // decodes the artwork and respects image orientation.
  try { // always releases the decoded source image.
    if (image.width * image.height > 48000000) throw new Error("please resize this image before uploading"); // bounds the canvas workload.
    const ratio: number = Math.min(1, 2400 / Math.max(image.width, image.height)); // retains enough detail for card exports.
    const canvas: HTMLCanvasElement = document.createElement("canvas"); // prepares a compact normalized image.
    canvas.width = Math.max(1, Math.round(image.width * ratio)); canvas.height = Math.max(1, Math.round(image.height * ratio)); // preserves artwork proportions.
    const context: CanvasRenderingContext2D | null = canvas.getContext("2d"); // obtains the image drawing surface.
    if (!context) throw new Error("image uploads are unavailable in this browser"); // handles missing canvas support.
    context.drawImage(image, 0, 0, canvas.width, canvas.height); // draws the normalized image.
    const blob: Blob = await new Promise((resolve, reject) => canvas.toBlob((result: Blob | null): void => result ? resolve(result) : reject(new Error("could not prepare this image")), "image/webp", 0.94)); // preserves visual detail while reducing transfer size.
    return { blob, width: canvas.width, height: canvas.height }; // returns the exact dimensions used by the preview.
  } finally { image.close(); } // releases image memory.
}
