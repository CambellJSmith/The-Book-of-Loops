import { install_standalone_cards } from "@/lib/server/card_set_repository"; // installs the authored collection through the application storage layer.
import { request_is_local, storage_failure } from "@/lib/server/storage"; // protects mutations and preserves recoverable errors.

export async function POST(request: Request): Promise<Response> { // performs the user-requested one-time collection installation.
  if (!request_is_local(request)) return Response.json({ error: "request origin is not allowed" }, { status: 403 }); // rejects cross-site requests before touching storage.
  try { // keeps all existing data intact if installation cannot complete.
    await install_standalone_cards(); // atomically imports the set or accepts an already completed installation.
    return Response.json({ installed: true }, { headers: { "Cache-Control": "private, no-store" } }); // confirms that the collection is ready to load.
  } catch (error: unknown) { // distinguishes identifier conflicts from temporary storage failures.
    if (String(error).includes("UNIQUE constraint failed")) return Response.json({ error: "the new set overlaps an existing species id; your existing cards have been preserved" }, { status: 409 }); // never replaces user-created records to install the set.
    return storage_failure(error, "could not prepare the card set; try again to resume safely"); // permits an idempotent retry after an interrupted request.
  }
}
