import { Flame, Droplet, Leaf, Sun, Moon, type LucideProps } from "lucide-react"; // reuses consistent elemental symbols.
import type { Element } from "@/lib/card_model"; // shares the available monster types.

export function ElementIcon({ element, ...props }: LucideProps & { element: Element }) { // selects a readable symbol for the current element.
  const Icon = { fire: Flame, water: Droplet, nature: Leaf, light: Sun, dark: Moon }[element]; // maps elements to their symbols.
  return <Icon aria-hidden="true" {...props} />; // keeps decorative icons out of the accessibility tree.
}
