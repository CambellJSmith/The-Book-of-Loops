"use client"; // makes the saved generation prompt editable and easy to copy.

import { type ChangeEvent } from "react"; // types the controlled text input.
import { Copy } from "lucide-react"; // identifies the clipboard action.
import { toast } from "sonner"; // reports clipboard success and recoverable errors.
import { Button } from "@/components/ui/button"; // preserves accessible action behavior.
import { Textarea } from "@/components/ui/textarea"; // reuses the existing multiline input primitive.

interface ArtPromptProps { value: string; disabled: boolean; change: (value: string) => void; } // exposes only the prompt field and its controlled update.
export function ArtPromptField({ value, disabled, change }: ArtPromptProps) { // keeps the image brief with its monster without printing it on the card.
  const copy_prompt = async (): Promise<void> => { // copies the complete self-contained generator prompt.
    try { await navigator.clipboard.writeText(value); toast.success("art prompt copied"); } // confirms the clipboard contains the current brief.
    catch { toast.error("could not copy; select the prompt text and copy it manually"); } // leaves a practical fallback when clipboard access is unavailable.
  };
  return ( // keeps the long prompt collapsed until it is needed.
    <details className="art_prompt_field">
      <summary>art_prompt</summary>
      <label className="field_label" htmlFor="art_prompt"><span>generation_prompt</span><Textarea id="art_prompt" value={value} disabled={disabled} maxLength={6000} rows={9} placeholder="describe the artwork to generate later" onChange={(event: ChangeEvent<HTMLTextAreaElement>) => change(event.target.value)} /></label>
      <Button type="button" variant="outline" size="sm" disabled={disabled || !value} onClick={() => void copy_prompt()}><Copy size={14} />copy_prompt</Button>
    </details>
  );
}
