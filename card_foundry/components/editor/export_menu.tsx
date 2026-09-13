"use client"; // exposes the available card output formats.

import { Braces, ChevronDown, Download, FileImage, Layers3, LoaderCircle, VectorSquare } from "lucide-react"; // distinguishes structured data, editable objects, and raster images.
import { Button } from "@/components/ui/button"; // preserves the existing export action styling.
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"; // provides keyboard-accessible export choices.

export type ExportFormat = "png" | "svg" | "json" | "collection_json"; // defines supported output actions without adding editor state.
interface ExportMenuProps { disabled: boolean; exporting: boolean; collection_disabled: boolean; export_file: (format: ExportFormat) => Promise<void>; } // connects the menu to the current snapshot export action.

export function ExportMenu({ disabled, exporting, collection_disabled, export_file }: ExportMenuProps) { // groups output formats around the card being exported.
  return ( // keeps export controls compact across desktop and mobile layouts.
    <DropdownMenu>
      <DropdownMenuTrigger asChild><Button className="export_button" disabled={disabled} aria-label="export card">{exporting ? <LoaderCircle className="spinning" /> : <Download />}<span>{exporting ? "exporting…" : "export"}</span><ChevronDown size={14} /></Button></DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={8} className="export_menu">
        <DropdownMenuLabel>current_card</DropdownMenuLabel>
        <DropdownMenuGroup>
          <DropdownMenuItem onSelect={() => void export_file("png")}><FileImage /><span><strong>png_image</strong><small>1500 × 2100 pixels</small></span></DropdownMenuItem>
          <DropdownMenuItem onSelect={() => void export_file("svg")}><VectorSquare /><span><strong>svg_objects</strong><small>editable text, shapes, and artwork</small></span></DropdownMenuItem>
          <DropdownMenuItem onSelect={() => void export_file("json")}><Braces /><span><strong>json_object</strong><small>monster data with embedded artwork</small></span></DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuLabel>saved_collection</DropdownMenuLabel>
        <DropdownMenuItem disabled={collection_disabled} onSelect={() => void export_file("collection_json")}><Layers3 /><span><strong>json_collection</strong><small>all saved cards and their artwork</small></span></DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
