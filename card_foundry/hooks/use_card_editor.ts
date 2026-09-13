"use client"; // manages the interactive card workspace.

import { useCallback, useEffect, useRef, useState } from "react"; // encapsulates editor state and async actions.
import { toast } from "sonner"; // shows brief recoverable feedback.
import { blank_card, card_schema, example_card, type MonsterCard } from "@/lib/card_model"; // shares the monster model.
import { api_request, load_cards, save_card } from "@/lib/card_api"; // accesses the saved collection.
import { prepare_art, type PreparedArt } from "@/lib/art_upload"; // validates uploaded artwork.

export function use_card_editor() { // keeps record management separate from presentation.
  const [card, set_card] = useState<MonsterCard>(example_card); // holds the visible draft.
  const [cards, set_cards] = useState<MonsterCard[]>([]); // holds saved collection records.
  const [baseline, set_baseline] = useState<string>(JSON.stringify(example_card)); // detects unsaved changes.
  const [loading, set_loading] = useState<boolean>(true); // tracks initial collection loading.
  const [load_error, set_load_error] = useState<string>(""); // retains retryable load failures.
  const [busy, set_busy] = useState<"" | "saving" | "uploading" | "deleting">(""); // prevents overlapping edits during writes.
  const [pending, set_pending] = useState<MonsterCard | null>(null); // holds a requested selection until changes are resolved.
  const touched = useRef<boolean>(false); // protects edits made while the collection loads.
  const lock = useRef<boolean>(false); // guards overlapping asynchronous writes.
  const dirty: boolean = JSON.stringify(card) !== baseline; // compares the current draft with its last accepted state.

  const accept_card = useCallback((next: MonsterCard): void => { // switches the draft and its saved baseline together.
    set_card(next); set_baseline(JSON.stringify(next)); set_pending(null); // updates the complete selected state.
  }, []);
  const reload = useCallback(async (): Promise<void> => { // reloads saved cards while protecting the active draft.
    set_loading(true); set_load_error(""); // begins a recoverable collection request.
    try { // keeps the editor usable if the collection is unavailable.
      const rows: MonsterCard[] = await load_cards(); // requests the latest saved collection.
      set_cards(rows); // refreshes the collection list.
      if (!touched.current && rows.length) accept_card(rows[0]); // opens the latest card only before editing begins.
    } catch (error: unknown) { set_load_error(error instanceof Error ? error.message : "could not load your cards"); } // retains a useful retry state.
    finally { set_loading(false); } // completes collection loading.
  }, [accept_card]);
  useEffect(() => { void reload(); }, [reload]); // loads saved cards on entry.
  useEffect(() => { // protects unsaved edits when closing or reloading the page.
    const guard = (event: BeforeUnloadEvent): void => { if (dirty || busy) { event.preventDefault(); event.returnValue = ""; } }; // asks the browser to protect active work.
    window.addEventListener("beforeunload", guard); // installs draft protection.
    return () => window.removeEventListener("beforeunload", guard); // removes stale handlers.
  }, [dirty, busy]);
  const update = useCallback((patch: Partial<MonsterCard>): void => { // applies controlled field changes.
    if (lock.current) return; // protects an in-flight write.
    touched.current = true; set_card((previous: MonsterCard) => ({ ...previous, ...patch })); // marks and updates the draft.
  }, []);
  const select = useCallback((next: MonsterCard): void => { // stages selection when the current card has edits.
    if (lock.current || loading) return; // avoids replacing a draft during a write or initial load.
    touched.current = true; // records deliberate navigation.
    if (dirty) set_pending(next); else accept_card(next); // protects unsaved changes before switching.
  }, [dirty, loading, accept_card]);
  const save = useCallback(async (): Promise<MonsterCard | null> => { // saves the complete draft and refreshes the collection.
    if (lock.current) return null; // prevents duplicate writes.
    const parsed = card_schema.safeParse(card); // validates required names and statistic ranges.
    if (!parsed.success) { toast.error(parsed.error.issues[0].message); return null; } // keeps invalid inputs available for correction.
    lock.current = true; set_busy("saving"); // locks the draft for the duration of the write.
    try { // retains all draft data when persistence fails.
      const saved: MonsterCard = await save_card(parsed.data); // writes the current record revision.
      accept_card(saved); set_cards((previous: MonsterCard[]) => [saved, ...previous.filter((item: MonsterCard) => item.id !== saved.id)]); // reflects the successful saved state.
      toast.success("card saved"); return saved; // confirms completion to the interface.
    } catch (error: unknown) { toast.error(error instanceof Error ? error.message : "could not save this card"); return null; } // keeps failed saves recoverable.
    finally { lock.current = false; set_busy(""); } // unlocks the editor.
  }, [card, accept_card]);
  const upload = useCallback(async (file: File): Promise<void> => { // uploads and attaches artwork without manual filenames.
    if (lock.current) return; // avoids concurrent artwork and card writes.
    lock.current = true; set_busy("uploading"); touched.current = true; // protects the upload destination.
    try { // leaves the previous artwork intact on failure.
      const prepared: PreparedArt = await prepare_art(file); // normalizes raster artwork.
      const form: FormData = new FormData(); form.append("art", prepared.blob, "artwork.webp"); // sends the prepared image bytes.
      const response: { art: string } = await api_request("/api/art", { method: "POST", body: form }); // saves the image asset.
      set_card((previous: MonsterCard) => ({ ...previous, art: response.art, art_width: prepared.width, art_height: prepared.height, art_zoom: 1, art_x: 50, art_y: 50 })); // attaches the new image with centered framing.
      toast.success("artwork attached — save your card to keep this change"); // distinguishes upload completion from saving the card.
    } catch (error: unknown) { toast.error(error instanceof Error ? error.message : "could not upload this image"); } // preserves the draft on upload failure.
    finally { lock.current = false; set_busy(""); } // unlocks the editor.
  }, []);
  const remove = useCallback(async (): Promise<void> => { // deletes the selected saved record after interface confirmation.
    if (lock.current || !card.revision) return; // skips unsaved drafts and overlapping writes.
    lock.current = true; set_busy("deleting"); // protects the deletion target.
    try { // leaves the card available if deletion fails.
      await api_request(`/api/cards/${card.id}?revision=${card.revision}`, { method: "DELETE" }); // deletes only the revision currently shown.
      const remaining: MonsterCard[] = cards.filter((item: MonsterCard) => item.id !== card.id); // updates the remaining collection.
      set_cards(remaining); accept_card(remaining[0] ?? blank_card(remaining)); toast.success("card deleted"); // opens the next available card.
    } catch (error: unknown) { toast.error(error instanceof Error ? error.message : "could not delete this card"); } // reports recoverable deletion failure.
    finally { lock.current = false; set_busy(""); } // releases the mutation lock.
  }, [card, cards, accept_card]);
  return { card, cards, dirty, loading, load_error, busy, pending, set_pending, accept_card, update, select, save, upload, remove, reload }; // exposes only the actions needed by the interface.
}
