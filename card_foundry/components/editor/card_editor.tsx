"use client"; // opens the interactive trading-card workspace.

import { useRef, useState, type CSSProperties } from "react"; // manages export references and confirmation dialogs.
import { Layers3, Save, SlidersHorizontal, Frame, Trash2, Check, LoaderCircle, PanelLeft, ShieldCheck } from "lucide-react"; // provides readable workspace action symbols.
import { toast, Toaster } from "sonner"; // presents short success and failure messages.
import { Button } from "@/components/ui/button"; // reuses accessible action primitives.
import { SidebarProvider } from "@/components/ui/sidebar"; // supports the saved-card sidebar.
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog"; // protects unsaved work and deletions.
import { CardPreview } from "./card_preview"; // renders the original trading-card design.
import { CardFields } from "./card_fields"; // exposes every requested monster field.
import { CardCollection } from "./card_collection"; // presents the saved collection.
import { use_card_editor } from "@/hooks/use_card_editor"; // encapsulates data and artwork actions.
import { card_schema, element_colors, type MonsterCard } from "@/lib/card_model"; // supplies validation and card colours.
import { export_card_png } from "@/lib/card_export"; // exports the same vector used by the preview.
import { ExportMenu, type ExportFormat } from "./export_menu"; // offers image, editable vector, and structured-object outputs.
import { export_card_svg } from "@/lib/exports/card_svg"; // exports editable card design objects.
import { export_card_objects } from "@/lib/exports/card_objects"; // exports portable monster data with embedded artwork.
import { card_filename } from "@/lib/exports/download"; // preserves descriptive filenames across formats.
import { load_cards } from "@/lib/card_api"; // exports a fresh copy of the saved collection.
import { use_editor_tools } from "@/hooks/use_editor_tools"; // exposes supported editor actions to compatible agents.

export function CardEditor() { // assembles the focused trading-card workspace.
  const editor = use_card_editor(); // owns the draft, collection, and save actions.
  const svg_ref = useRef<SVGSVGElement>(null); // identifies the exact preview to export.
  const export_lock = useRef<boolean>(false); // prevents duplicate export requests before the next render.
  const [exporting, set_exporting] = useState<boolean>(false); // prevents overlapping PNG exports.
  const [delete_open, set_delete_open] = useState<boolean>(false); // holds the deletion confirmation state.
  const [show_collection, set_show_collection] = useState<boolean>(false); // toggles the collection panel on small screens.
  const disabled: boolean = Boolean(editor.busy) || exporting; // prevents edits while a snapshot is being saved or exported.
  use_editor_tools(editor, exporting); // registers the same actions used by the visible interface.
  const export_file = async (format: ExportFormat): Promise<void> => { // exports the selected card representation without mutating saved data.
    if (disabled || export_lock.current) return; // prevents overlapping exports and in-flight writes.
    const parsed = format === "collection_json" ? null : card_schema.safeParse(editor.card); // validates the visible draft only when it is the export target.
    if (parsed && !parsed.success) { toast.error(parsed.error.issues[0].message); return; } // preserves incomplete drafts for correction.
    export_lock.current = true; set_exporting(true); // freezes the export snapshot and related controls.
    const toast_id: string | number = toast.loading("preparing your export…"); // provides feedback while artwork is being embedded.
    const progress = (completed: number, total: number): void => { toast.loading(total ? `embedding artwork ${completed} of ${total}…` : "preparing card objects…", { id: toast_id }); }; // reports collection progress without exposing implementation details.
    try { // keeps download failures recoverable.
      if (format === "collection_json") { // exports persisted collection data, including images shared by several cards.
        const cards: MonsterCard[] = await load_cards(); // reads the latest saved collection without changing the active draft.
        const count: number = await export_card_objects(cards, "card_collection.json", progress); // includes every saved card in one portable JSON document.
        toast.success(`${count} saved ${count === 1 ? "card" : "cards"} exported as json`, { id: toast_id }); // reports the actual number of exported cards.
      } else if (parsed?.success) { // exports the complete current draft in the selected format.
        if (format === "json") { // exports game data independently from the visual card layout.
          await export_card_objects([parsed.data], card_filename(parsed.data, "json"), progress); // embeds the card's artwork with its structured fields.
          toast.success("json exported with monster data and artwork", { id: toast_id }); // confirms the portable object download.
        } else { // exports the visual card using the existing preview geometry.
          if (!svg_ref.current) throw new Error("wait for the card preview to finish loading"); // avoids generating an empty visual export.
          if (format === "svg") await export_card_svg(svg_ref.current, parsed.data); else await export_card_png(svg_ref.current, parsed.data); // selects editable objects or the established raster format.
          toast.success(format === "svg" ? "svg exported with editable objects and embedded artwork" : "png exported · 1500 × 2100 px", { id: toast_id }); // describes the downloaded format.
        }
      }
    } catch (error: unknown) { toast.error(error instanceof Error ? error.message : "could not export these cards", { id: toast_id }); } // keeps the current draft and collection unchanged on failure.
    finally { export_lock.current = false; set_exporting(false); } // restores normal editing after the export completes.
  };
  const select = (card: MonsterCard): void => { editor.select(card); set_show_collection(false); }; // returns mobile users to their selected card.
  return ( // keeps the primary creation flow visible in the first viewport.
    <div className="card_app" style={{ "--card-accent": element_colors[editor.card.type] } as CSSProperties}>
      <header className="app_header"><div className="brand"><span className="brand_mark"><Layers3 size={23} /></span><h1>card<span>_foundry</span></h1><span className="workspace_badge">studio</span></div><div className="header_actions"><span className="save_status" aria-live="polite">{editor.busy === "saving" ? <><LoaderCircle size={14} className="spinning" />saving…</> : editor.dirty ? "unsaved changes" : editor.card.revision ? <><Check size={14} />saved</> : "unsaved card"}</span><Button variant="outline" className="save_button" disabled={disabled || editor.loading} onClick={() => void editor.save()}><Save />save_card</Button><ExportMenu disabled={disabled} exporting={exporting} collection_disabled={editor.loading || Boolean(editor.load_error) || !editor.cards.length} export_file={export_file} /></div></header>
      <SidebarProvider className={`workspace ${show_collection ? "show_collection" : ""}`} style={{ "--sidebar-width": "232px" } as CSSProperties}>
        <CardCollection cards={editor.cards} current={editor.card} loading={editor.loading} error={editor.load_error} disabled={disabled} select={select} reload={editor.reload} close={() => set_show_collection(false)} />
        <main className="preview_panel"><div className="panel_heading preview_heading"><div><Button className="mobile_collection_toggle" variant="ghost" size="icon-sm" aria-label="toggle card collection" onClick={() => set_show_collection(!show_collection)}><PanelLeft /></Button><Frame size={15} /><span>card_preview</span></div><span className="live_label">live</span></div><div className="preview_stage"><div className="stage_title"><span>#{editor.card.species_id || "0000"}</span><span>{editor.card.species_name || "untitled monster"}</span></div><div className="card_mount"><CardPreview card={editor.card} svg_ref={svg_ref} /></div><div className="preview_caption"><span className="caption_line" /><span>original frame / {editor.card.type}</span><span className="caption_line" /></div></div><div className="preview_toolbar"><span><Frame size={14} />1500 × 2100 px</span><span>png / svg / json</span><Button variant="ghost" size="icon-sm" aria-label="delete selected saved card" title="delete saved card" disabled={disabled || !editor.card.revision} onClick={() => set_delete_open(true)}><Trash2 size={15} /></Button></div></main>
        <aside className="inspector_panel" aria-label="card properties"><div className="panel_heading"><div><SlidersHorizontal size={15} /><span>card_properties</span></div><span className="property_count">monster</span></div><CardFields card={editor.card} disabled={disabled} uploading={editor.busy === "uploading"} update={editor.update} upload={editor.upload} /></aside>
      </SidebarProvider>
      <footer className="status_bar"><span><ShieldCheck size={12} />your card studio</span><span>{editor.cards.length} saved {editor.cards.length === 1 ? "card" : "cards"}<span className="footer_divider">/</span>{editor.card.type}</span><span>edit · save · create</span></footer>
      <AlertDialog open={Boolean(editor.pending)} onOpenChange={(open: boolean) => { if (!open) editor.set_pending(null); }}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>save your changes?</AlertDialogTitle><AlertDialogDescription>This card has unsaved changes. Save it before opening another card, or discard this draft.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel disabled={disabled}>keep_editing</AlertDialogCancel><Button variant="outline" disabled={disabled} onClick={() => { if (editor.pending) editor.accept_card(editor.pending); }}>discard_changes</Button><Button disabled={disabled} onClick={async () => { const next: MonsterCard | null = editor.pending; const saved: MonsterCard | null = await editor.save(); if (saved && next) editor.accept_card(next.id === saved.id ? saved : next); }}>save_and_continue</Button></AlertDialogFooter></AlertDialogContent></AlertDialog>
      <AlertDialog open={delete_open} onOpenChange={set_delete_open}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>delete {editor.card.species_name}?</AlertDialogTitle><AlertDialogDescription>This removes the saved card from your collection. This action cannot be undone.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>keep_card</AlertDialogCancel><AlertDialogAction variant="destructive" onClick={() => void editor.remove()}>delete_card</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
      <Toaster theme="dark" position="bottom-center" richColors closeButton />
    </div>
  );
}
