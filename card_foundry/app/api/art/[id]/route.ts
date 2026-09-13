import { z } from "zod"; // validates artwork identifiers.
import { artwork_bucket, storage_failure } from "@/lib/server/storage"; // accesses persisted artwork safely.

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> { // streams artwork without loading full objects into memory.
  const { id } = await context.params; // resolves the requested artwork identifier.
  if (!z.string().uuid().safeParse(id).success) return new Response("artwork not found", { status: 404 }); // rejects malformed object references.
  try { // reports storage outages separately from missing artwork.
    const object = await artwork_bucket().get(`art/${id}`); // fetches the artwork stream.
    if (!object) return new Response("artwork not found", { status: 404 }); // handles deleted or unknown assets.
    const headers: Headers = new Headers({ "Cache-Control": "private, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff", "Content-Disposition": "inline" }); // safely caches immutable images in the user's browser.
    object.writeHttpMetadata(headers); headers.set("ETag", object.httpEtag); // retains the verified image content type and identity.
    return new Response(object.body, { headers }); // streams the saved raster bytes.
  } catch (error: unknown) { return storage_failure(error, "artwork is temporarily unavailable"); } // reports retryable artwork failures.
}
