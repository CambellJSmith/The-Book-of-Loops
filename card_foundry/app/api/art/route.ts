import { artwork_bucket, request_is_local, storage_failure } from "@/lib/server/storage"; // owns artwork storage and write boundaries.

function image_type(bytes: Uint8Array): string | null { // verifies raster signatures instead of trusting file extensions.
  if (bytes.length >= 12 && bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46 && bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50) return "image/webp"; // recognizes WebP containers.
  if (bytes.length >= 8 && [137, 80, 78, 71, 13, 10, 26, 10].every((value: number, index: number) => value === bytes[index])) return "image/png"; // recognizes PNG files.
  if (bytes.length >= 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return "image/jpeg"; // recognizes JPEG files.
  return null; // rejects unsupported and active formats.
}
export async function POST(request: Request): Promise<Response> { // stores artwork and returns its stable reference.
  if (!request_is_local(request)) return Response.json({ error: "request origin is not allowed" }, { status: 403 }); // blocks cross-site browser uploads.
  if (Number(request.headers.get("content-length") || 0) > 9 * 1024 * 1024) return Response.json({ error: "please use a smaller artwork image" }, { status: 413 }); // rejects oversized announced uploads.
  try { // keeps failed uploads recoverable.
    const form: FormData = await request.formData(); // reads the uploaded artwork.
    const file: FormDataEntryValue | null = form.get("art"); // selects the expected file field.
    if (!(file instanceof File) || !file.size || file.size > 8 * 1024 * 1024) return Response.json({ error: "choose a valid artwork image smaller than 8 mb after resizing" }, { status: 400 }); // enforces bounded image uploads.
    const bytes: ArrayBuffer = await file.arrayBuffer(); // reads the normalized raster bytes.
    const content_type: string | null = image_type(new Uint8Array(bytes)); // checks the actual file format.
    if (!content_type) return Response.json({ error: "choose a png, jpg, or webp image" }, { status: 400 }); // rejects unsupported files.
    const id: string = crypto.randomUUID(); // attaches artwork without requiring manual filenames.
    await artwork_bucket().put(`art/${id}`, bytes, { httpMetadata: { contentType: content_type }, customMetadata: { original_name: file.name } }); // persists the artwork with verified metadata.
    return Response.json({ art: `/api/art/${id}` }, { status: 201 }); // returns the stable same-origin image reference.
  } catch (error: unknown) { return storage_failure(error, "could not upload your artwork; please try again"); } // retains the previous image on failure.
}
