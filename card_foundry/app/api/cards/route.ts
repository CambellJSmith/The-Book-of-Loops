import { read_cards } from "@/lib/server/card_repository"; // loads the durable card collection.
import { storage_failure } from "@/lib/server/storage"; // provides recoverable storage errors.

export async function GET(): Promise<Response> { // serves the saved collection to the editor.
  try { return Response.json({ cards: await read_cards() }, { headers: { "Cache-Control": "private, no-store" } }); } // prevents stale collection responses.
  catch (error: unknown) { return storage_failure(error, "could not load your cards; your draft is still here. try again."); } // preserves the editor during outages.
}
