import { z } from "zod"; // validates request identifiers.
import { card_schema } from "@/lib/card_model"; // checks all user-supplied card fields.
import { delete_card, write_card } from "@/lib/server/card_repository"; // owns atomic record mutations.
import { artwork_bucket, request_is_local, storage_failure } from "@/lib/server/storage"; // protects and diagnoses storage writes.

type RouteContext = { params: Promise<{ id: string }> }; // describes the route's record identifier.
export async function PUT(request: Request, context: RouteContext): Promise<Response> { // saves a complete validated card.
  if (!request_is_local(request)) return Response.json({ error: "request origin is not allowed" }, { status: 403 }); // blocks cross-site browser writes.
  if (!request.headers.get("content-type")?.includes("application/json")) return Response.json({ error: "send card data as json" }, { status: 415 }); // accepts only the expected request format.
  if (Number(request.headers.get("content-length") || 0) > 16000) return Response.json({ error: "card data is too large" }, { status: 413 }); // bounds announced request size.
  const { id } = await context.params; // resolves the selected record identifier.
  const text: string = await request.text(); // reads the compact card payload.
  if (text.length > 16000) return Response.json({ error: "card data is too large" }, { status: 413 }); // bounds payloads without an announced length.
  let raw: unknown; // holds untrusted request data before validation.
  try { raw = JSON.parse(text); } catch { return Response.json({ error: "card data could not be read" }, { status: 400 }); } // rejects malformed JSON.
  const parsed = card_schema.safeParse(raw); // validates every card field and artwork reference.
  if (!parsed.success) return Response.json({ error: parsed.error.issues[0].message }, { status: 400 }); // returns an actionable field error.
  if (id !== parsed.data.id) return Response.json({ error: "the card identifier does not match" }, { status: 400 }); // prevents record-target confusion.
  try { // preserves a recoverable boundary around persistence.
    if (parsed.data.art.startsWith("/api/art/")) { // verifies uploaded artwork before saving its reference.
      const art = await artwork_bucket().head(`art/${parsed.data.art.split("/").pop()}`); // checks the actual object exists.
      if (!art) return Response.json({ error: "please upload your artwork again before saving" }, { status: 400 }); // avoids broken saved artwork references.
    }
    const card = await write_card(parsed.data); // atomically writes the expected record revision.
    if (!card) return Response.json({ error: "this card changed in another tab. keep your edits, reload the collection, and reopen the saved card before editing again." }, { status: 409 }); // preserves newer changes and the user's draft.
    return Response.json({ card }, { headers: { "Cache-Control": "no-store" } }); // returns the authoritative saved revision.
  } catch (error: unknown) { // maps storage constraints into clear errors.
    if (String(error).includes("UNIQUE constraint failed")) return Response.json({ error: "that species id is already in use; choose a different id" }, { status: 409 }); // explains duplicate species numbering.
    return storage_failure(error, "could not save your card; your changes are still here. try again."); // keeps failed saves recoverable.
  }
}
export async function DELETE(request: Request, context: RouteContext): Promise<Response> { // deletes a confirmed saved card.
  if (!request_is_local(request)) return Response.json({ error: "request origin is not allowed" }, { status: 403 }); // blocks cross-site browser writes.
  const { id } = await context.params; // resolves the selected card identifier.
  const revision: number = Number(new URL(request.url).searchParams.get("revision")); // reads the reviewed card revision.
  if (!z.string().uuid().safeParse(id).success || !Number.isInteger(revision) || revision < 1) return Response.json({ error: "choose a saved card to delete" }, { status: 400 }); // validates the deletion target.
  try { // handles storage outages without losing the visible record.
    if (!await delete_card(id, revision)) return Response.json({ error: "this card changed or was already deleted; reload your collection" }, { status: 409 }); // prevents deletion of a newer record.
    return Response.json({ deleted: true }); // confirms completion.
  } catch (error: unknown) { return storage_failure(error, "could not delete your card; please try again"); } // reports recoverable deletion failures.
}
