"use client"; // enables collection selection and retry actions.

import { Layers3, Plus, RefreshCw, ImageIcon, X } from "lucide-react"; // supplies collection action symbols.
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar"; // uses accessible sidebar primitives.
import { Button } from "@/components/ui/button"; // supplies standard action controls.
import { Skeleton } from "@/components/ui/skeleton"; // distinguishes loading from an empty collection.
import { ElementIcon } from "./element_icon"; // identifies each saved card's element.
import { blank_card, example_card, element_colors, type MonsterCard } from "@/lib/card_model"; // shares collection records while encounter difficulty remains internal.

interface CollectionProps { cards: MonsterCard[]; current: MonsterCard; loading: boolean; error: string; disabled: boolean; select: (card: MonsterCard) => void; reload: () => Promise<void>; close: () => void; } // describes collection data and actions.
export function CardCollection({ cards, current, loading, error, disabled, select, reload, close }: CollectionProps) { // presents saved cards without exposing internal progression metadata.
  const sorted_cards: MonsterCard[] = [...cards].sort((left: MonsterCard, right: MonsterCard) => left.species_id.localeCompare(right.species_id)); // keeps the collection in stable species order.
  const card_item = (card: MonsterCard) => <SidebarMenuItem key={card.id}><SidebarMenuButton className="saved_card_item" isActive={current.id === card.id} disabled={disabled} onClick={() => select(card)} aria-label={`open ${card.species_name}, species ${card.species_id}${card.is_final_boss ? ", final boss" : ""}`}><span className="collection_art" style={{ borderColor: element_colors[card.type] }}>{card.art ? <img src={card.art} alt="" loading="lazy" /> : <ImageIcon size={19} />}</span><span className="collection_card_text"><strong>{card.species_name}</strong><span>#{card.species_id}{card.is_final_boss ? " · final boss" : ""}</span><small style={{ color: element_colors[card.type] }}><ElementIcon element={card.type} size={12} />{card.type}</small></span></SidebarMenuButton></SidebarMenuItem>; // renders one saved monster with player-facing information only.
  return ( // composes the collection panel from sidebar primitives.
    <Sidebar collapsible="none" className="collection_panel" aria-label="card collection">
      <SidebarHeader className="collection_heading"><span><Layers3 size={16} />my_cards <small>{cards.length.toString().padStart(2, "0")}</small></span><Button variant="ghost" size="icon-sm" aria-label="reload saved collection" title="reload collection" disabled={disabled || loading} onClick={() => void reload()}><RefreshCw size={14} className={loading ? "spinning" : ""} /></Button></SidebarHeader>
      <Button variant="ghost" className="close_collection" onClick={close}><X size={16} />close_collection</Button>
      <SidebarContent className="collection_content">
        <Button variant="outline" className="new_card_button" disabled={disabled || loading} onClick={() => select(blank_card([...cards, current]))}><Plus size={17} />new_card</Button>
        <div className="collection_caption">species_order</div>
        {loading ? <div className="collection_loading"><Skeleton className="h-20 w-full" /><span>loading your cards…</span></div> : error ? <div className="collection_error" role="alert"><p>{error}</p><Button variant="outline" size="sm" onClick={() => void reload()}>try_again</Button></div> : sorted_cards.length ? <SidebarMenu>{sorted_cards.map(card_item)}</SidebarMenu> : null}
        {!loading && !error && !cards.length && <div className="collection_empty"><Layers3 size={28} strokeWidth={1.2} /><strong>your collection starts here</strong><p>save a card to keep it here and edit it later.</p></div>}
        {!loading && <div className="example_area"><div className="collection_caption">starting_point</div><button className="example_card_button" disabled={disabled} onClick={() => select({ ...example_card, id: crypto.randomUUID(), species_id: blank_card(cards).species_id })}><img src="/sample_art.webp" alt="cindrel example artwork" /><span><strong>cindrel</strong><small>editable example</small></span><ElementIcon element="fire" size={15} /></button></div>}
      </SidebarContent>
      <SidebarFooter className="collection_footer"><span className="element_spectrum">{(["fire", "water", "nature", "light", "dark"] as const).map((element) => <ElementIcon key={element} element={element} size={15} style={{ color: element_colors[element] }} />)}</span><span>five types.</span></SidebarFooter>
    </Sidebar>
  );
}
