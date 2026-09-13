import { env } from "cloudflare:workers"; // accesses platform-owned storage only on the server.

export function database(): D1Database { // keeps database access behind one boundary.
  if (!env.DB) throw new Error("card database unavailable"); // reports missing storage to the request boundary.
  return env.DB; // returns the configured database.
}
export function artwork_bucket(): R2Bucket { // centralizes artwork storage access.
  if (!env.BUCKET) throw new Error("artwork storage unavailable"); // reports unavailable uploads.
  return env.BUCKET; // returns the configured object bucket.
}
export function request_is_local(request: Request): boolean { // rejects cross-site mutation attempts.
  const origin: string | null = request.headers.get("origin"); // reads browser origin context.
  return request.headers.get("sec-fetch-site") !== "cross-site" && (!origin || origin === new URL(request.url).origin); // accepts only same-origin browser writes.
}
export function storage_failure(error: unknown, message: string): Response { // keeps server diagnostics separate from useful user errors.
  console.error("card_foundry storage request failed", error); // records the underlying failure for diagnosis.
  return Response.json({ error: message }, { status: 503 }); // returns a retryable application error.
}
