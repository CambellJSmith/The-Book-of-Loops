"use client"; // provides controlled card-editing inputs.

import { useRef, useState, type CSSProperties, type ChangeEvent } from "react"; // manages file selection and drop feedback.
import { ImagePlus, Upload, RotateCcw, X, Heart, Zap, ChevronDown } from "lucide-react"; // supplies consistent control icons.
import { Button } from "@/components/ui/button"; // reuses accessible action controls.
import { Input } from "@/components/ui/input"; // reuses the shared text-input primitive.
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"; // exposes keyboard-accessible type selection.
import { Slider } from "@/components/ui/slider"; // provides artwork framing controls.
import { ArtPromptField } from "./art_prompt_field"; // keeps prompt editing separate from upload and crop controls.
import { ElementIcon } from "./element_icon"; // renders the five elemental symbols.
import { difficulties, difficulty_labels, elements, element_colors, type Difficulty, type MonsterCard, type Move, type Element } from "@/lib/card_model"; // shares field types, progression labels and palette rules.

interface FieldsProps { card: MonsterCard; disabled: boolean; uploading: boolean; update: (patch: Partial<MonsterCard>) => void; upload: (file: File) => Promise<void>; } // limits field access to controlled editor actions.

function NumberField({ id, label, value, change }: { id: string; label: string; value: number; change: (value: number) => void }) { // standardizes whole-number statistic inputs.
  return <label className="field_label" htmlFor={id}><span>{label}</span><Input id={id} type="number" min="0" max="9999" step="1" value={value} onChange={(event: ChangeEvent<HTMLInputElement>) => change(Math.max(0, Math.min(9999, Math.trunc(Number(event.target.value) || 0))))} className="number_input" /></label>; // keeps statistics within supported whole-number bounds.
}
export function CardFields({ card, disabled, uploading, update, upload }: FieldsProps) { // edits all requested card attributes.
  const file_ref = useRef<HTMLInputElement>(null); // opens the native artwork picker.
  const [dragging, set_dragging] = useState<boolean>(false); // highlights the artwork drop target.
  const update_move = (index: 0 | 1, patch: Partial<Move>): void => { // edits a move while preserving its sibling.
    const moves: [Move, Move] = [{ ...card.moves[0] }, { ...card.moves[1] }]; // copies the independent move slots.
    moves[index] = { ...moves[index], ...patch }; update({ moves }); // updates the chosen move.
  };
  return ( // groups the property controls into readable sections.
    <fieldset className="inspector_fields" disabled={disabled}>
      <section className="property_section">
        <h3><ChevronDown size={14} /><span>identity</span><span className="section_index">01</span></h3>
        <div className="identity_fields"><label className="field_label" htmlFor="species_id"><span>species_id</span><Input id="species_id" value={card.species_id} maxLength={20} onChange={(event: ChangeEvent<HTMLInputElement>) => update({ species_id: event.target.value })} placeholder="0001" /></label><label className="field_label" htmlFor="species_name"><span>species_name</span><Input id="species_name" value={card.species_name} maxLength={40} onChange={(event: ChangeEvent<HTMLInputElement>) => update({ species_name: event.target.value })} placeholder="name your monster" /></label></div>
        <div className="field_label"><span id="type_label">type</span><RadioGroup className="type_picker" value={card.type} onValueChange={(value: string) => update({ type: value as Element })} aria-labelledby="type_label" disabled={disabled}>{elements.map((element: Element) => <label key={element} className={`type_option ${card.type === element ? "selected" : ""}`} style={{ "--element": element_colors[element] } as CSSProperties}><RadioGroupItem value={element} className="sr-only" aria-label={element} /><ElementIcon element={element} size={20} /><span>{element}</span></label>)}</RadioGroup></div>
        <div className="two_fields mt-[15px]"><label className="field_label" htmlFor="difficulty"><span>difficulty</span><select id="difficulty" value={card.difficulty} onChange={(event: ChangeEvent<HTMLSelectElement>) => update({ difficulty: event.target.value as Difficulty })} className="h-[34px] w-full rounded-[4px] border border-[#454851] bg-[#202226] px-[9px] text-[0.875rem] text-[#e2e3e8] outline-none focus:border-[#e7a16c] focus:shadow-[0_0_0_1px_#e7a16c60]">{difficulties.map((difficulty: Difficulty) => <option key={difficulty} value={difficulty}>{difficulty_labels[difficulty]}</option>)}</select></label><div className="field_label"><span>encounter_role</span><div className="flex h-[34px] items-center rounded-[4px] border border-[#454851] bg-[#202226] px-[9px] text-[0.875rem] text-[#bcbfc8]">{card.is_final_boss ? "final boss" : "standard"}</div></div></div>
      </section>
      <section className="property_section">
        <h3><ChevronDown size={14} /><span>artwork</span><span className="section_index">02</span></h3>
        <input ref={file_ref} className="sr-only" type="file" id="artwork_file" accept="image/png,image/jpeg,image/webp" onChange={(event: ChangeEvent<HTMLInputElement>) => { const file: File | undefined = event.target.files?.[0]; if (file) void upload(file); event.target.value = ""; }} disabled={disabled} tabIndex={-1} aria-label="upload monster artwork" />
        <button type="button" className={`art_drop ${dragging ? "dragging" : ""}`} onClick={() => file_ref.current?.click()} disabled={disabled} onDragOver={(event) => { event.preventDefault(); if (!disabled) set_dragging(true); }} onDragLeave={() => set_dragging(false)} onDrop={(event) => { event.preventDefault(); set_dragging(false); const file: File | undefined = event.dataTransfer.files[0]; if (file && !disabled) void upload(file); }}>
          {card.art ? <img src={card.art} alt="current monster artwork" className="art_thumbnail" /> : <span className="upload_symbol"><ImagePlus size={25} /></span>}
          <span className="upload_copy"><strong>{uploading ? "uploading…" : card.art ? "replace_artwork" : "upload_artwork"}</strong><span>drop an image or browse</span><small>png, jpg, webp · up to 20 mb</small></span><Upload size={16} className="upload_arrow" />
        </button>
        <ArtPromptField value={card.art_prompt} disabled={disabled} change={(art_prompt: string) => update({ art_prompt })} />
        {card.art && <div className="art_controls"><details><summary>adjust_framing <ChevronDown size={14} /></summary><div className="framing_sliders">{([{ field: "art_zoom", label: "zoom", min: 1, max: 3, step: 0.01 }, { field: "art_x", label: "horizontal", min: 0, max: 100, step: 1 }, { field: "art_y", label: "vertical", min: 0, max: 100, step: 1 }] as const).map((control) => <div className="slider_field" key={control.field}><span id={`${control.field}_label`}>{control.label}</span><Slider value={[card[control.field]]} min={control.min} max={control.max} step={control.step} onValueChange={(values: number[]) => update({ [control.field]: values[0] })} aria-labelledby={`${control.field}_label`} disabled={disabled} /><output>{control.field === "art_zoom" ? `${Math.round(card.art_zoom * 100)}%` : card[control.field]}</output></div>)}<Button type="button" variant="ghost" size="sm" onClick={() => update({ art_zoom: 1, art_x: 50, art_y: 50 })}><RotateCcw />reset_framing</Button></div></details><Button variant="ghost" size="icon-sm" aria-label="remove artwork from this card" title="remove artwork" onClick={() => update({ art: "" })}><X size={14} /></Button></div>}
      </section>
      <section className="property_section">
        <h3><ChevronDown size={14} /><span>base_stats</span><span className="section_index">03</span></h3>
        <div className="two_fields"><div className="stat_field"><Heart size={14} /><NumberField id="health" label="health" value={card.health} change={(value: number) => update({ health: value })} /></div><div className="stat_field"><Zap size={14} /><NumberField id="speed" label="speed" value={card.speed} change={(value: number) => update({ speed: value })} /></div></div>
      </section>
      <section className="property_section moves_section">
        <h3><ChevronDown size={14} /><span>moves</span><span className="section_index">04</span></h3>
        {card.moves.map((move: Move, index: number) => <div key={index} className="move_fields"><div className="move_heading"><span className="move_number">0{index + 1}</span><span>move_{index + 1}</span></div><label className="field_label" htmlFor={`move_${index}_name`}><span>name</span><Input id={`move_${index}_name`} value={move.name} maxLength={36} placeholder="name this move" onChange={(event: ChangeEvent<HTMLInputElement>) => update_move(index as 0 | 1, { name: event.target.value })} /></label><div className="two_fields"><NumberField id={`move_${index}_mana`} label="mana_cost" value={move.mana_cost} change={(value: number) => update_move(index as 0 | 1, { mana_cost: value })} /><NumberField id={`move_${index}_damage`} label="damage" value={move.damage} change={(value: number) => update_move(index as 0 | 1, { damage: value })} /></div></div>)}
      </section>
    </fieldset>
  );
}
