"use client"; // registers editor tools only in compatible browsers.

import { useEffect, useRef } from "react"; // keeps tool callbacks synchronized with the visible draft.
import { flushSync } from "react-dom"; // finishes visible state updates before reporting success.
import { card_schema, type MonsterCard } from "@/lib/card_model"; // shares validation with normal editor controls.
import type { use_card_editor } from "./use_card_editor"; // reuses the actual editor action contract.

interface ToolDefinition { name: string; description: string; inputSchema: object; annotations: { readOnlyHint: boolean; untrustedContentHint: boolean }; execute: (input: unknown) => unknown | Promise<unknown>; } // describes supported page-scoped tools.
interface ModelContext { registerTool: (tool: ToolDefinition, options: { signal: AbortSignal }) => void | Promise<void>; } // feature-detects the optional browser registry.
type Editor = ReturnType<typeof use_card_editor>; // connects tools to the same state used by the interface.
const patch_schema = card_schema.omit({ id: true, revision: true, art: true, art_width: true, art_height: true }).partial().strict(); // limits agent edits to visible text, statistics, type, and framing.

export function use_editor_tools(editor: Editor, exporting: boolean): void { // adds optional agent access to real editor actions.
  const current = useRef<{ editor: Editor; exporting: boolean }>({ editor, exporting }); // retains current state without repeated registration.
  current.current = { editor, exporting }; // refreshes action references during every render.
  useEffect(() => { // registers each action once for the page lifetime.
    const context: ModelContext | undefined = (document as Document & { modelContext?: ModelContext }).modelContext; // checks optional browser support.
    if (!context?.registerTool) return; // leaves unsupported browsers unaffected.
    const lifecycle: AbortController = new AbortController(); // owns all tool registrations.
    const tools: ToolDefinition[] = [ // exposes only meaningful card-editor journeys.
      { name: "read_card_editor", description: "Read the current monster draft, unsaved status, and saved collection.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true, untrustedContentHint: true }, execute: () => ({ card: current.current.editor.card, unsaved_changes: current.current.editor.dirty, saved_cards: current.current.editor.cards, busy: Boolean(current.current.editor.busy) || current.current.exporting }) }, // reads state without mutation.
      { name: "stage_card_edits", description: "Update fields in the visible monster draft. This does not save the card; use save_current_card to persist it.", inputSchema: { type: "object", properties: { species_id: { type: "string", minLength: 1, maxLength: 20 }, species_name: { type: "string", minLength: 1, maxLength: 40 }, type: { type: "string", enum: ["fire", "water", "nature", "light", "dark"] }, health: { type: "integer", minimum: 0, maximum: 9999 }, speed: { type: "integer", minimum: 0, maximum: 9999 }, moves: { type: "array", minItems: 2, maxItems: 2, items: { type: "object", properties: { name: { type: "string", minLength: 1, maxLength: 36 }, mana_cost: { type: "integer", minimum: 0, maximum: 9999 }, damage: { type: "integer", minimum: 0, maximum: 9999 } }, required: ["name", "mana_cost", "damage"], additionalProperties: false } }, art_zoom: { type: "number", minimum: 1, maximum: 3 }, art_x: { type: "number", minimum: 0, maximum: 100 }, art_y: { type: "number", minimum: 0, maximum: 100 } }, additionalProperties: false }, annotations: { readOnlyHint: false, untrustedContentHint: true }, execute: (input: unknown) => { // stages the same changes as editing the form.
        if (current.current.editor.busy || current.current.editor.loading || current.current.exporting) throw new Error("wait for the current action to finish"); // protects in-flight work.
        const patch: Partial<MonsterCard> = patch_schema.parse(input); // rejects unsupported or invalid edits.
        flushSync(() => current.current.editor.update(patch)); // commits the same state change used by the form.
        return { card: current.current.editor.card, status: "draft_updated" }; // reports the visible updated draft.
      } },
      { name: "save_current_card", description: "Validate and save the visible monster draft to the saved collection.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations: { readOnlyHint: false, untrustedContentHint: true }, execute: async () => { // completes the normal save action.
        if (current.current.editor.busy || current.current.editor.loading || current.current.exporting) throw new Error("wait for the current action to finish"); // prevents overlapping state changes.
        const saved: MonsterCard | null = await current.current.editor.save(); // persists through the same checked API.
        if (!saved) throw new Error("card was not saved; review the visible validation or save error"); // reports intentional save failures.
        flushSync(() => undefined); // flushes any pending visible save updates.
        return { id: saved.id, species_id: saved.species_id, revision: saved.revision, status: "saved" }; // returns the actual persisted revision.
      } },
    ];
    for (const tool of tools) { // installs the supported editor actions.
      try { void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch((error: unknown) => console.warn("editor tool registration unavailable", error)); } // handles asynchronous registration failures.
      catch (error: unknown) { console.warn("editor tool registration unavailable", error); } // preserves normal editing on unsupported registries.
    }
    return () => lifecycle.abort(); // unregisters tools when leaving the editor.
  }, []);
}
