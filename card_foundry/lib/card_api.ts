import { card_schema, type MonsterCard } from "./card_model"; // validates saved and loaded cards.

export async function api_request<T>(url: string, init?: RequestInit): Promise<T> { // centralizes recoverable request failures.
  const response: Response = await fetch(url, { ...init, cache: "no-store" }); // requests the current saved state.
  const payload: T & { error?: string } = await response.json().catch(() => ({ error: "the request could not be completed; please try again" })) as T & { error?: string }; // handles non-JSON failures before record-level validation.
  if (!response.ok || payload.error) throw new Error(payload.error || "the request could not be completed"); // exposes clear errors to the editor.
  return payload; // returns the successful response.
}
export async function load_cards(): Promise<MonsterCard[]> { // fetches the saved collection.
  await api_request("/api/card_sets/standalone_400", { method: "POST" }); // installs the requested set once without replacing later edits or deletions.
  const response: { cards: unknown[] } = await api_request("/api/cards"); // loads persisted monster records.
  return response.cards.map((card: unknown) => card_schema.parse(card)); // rejects malformed saved data.
}
export async function save_card(card: MonsterCard): Promise<MonsterCard> { // persists a validated monster without losing newer revisions.
  const parsed: MonsterCard = card_schema.parse(card); // checks fields before submitting.
  const response: { card: unknown } = await api_request(`/api/cards/${parsed.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parsed) }); // saves the current revision.
  return card_schema.parse(response.card); // checks and returns the saved record.
}
