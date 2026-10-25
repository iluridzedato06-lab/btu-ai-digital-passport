
const API = process.env.API_INTERNAL_URL || "http://localhost:8000";

/** Server-side fetch of public JSON. Returns null when the API is unreachable. */
export async function serverGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API}/api${path}`, { cache: "no-store", headers: { Accept: "application/json" } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
