const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem("csj_token");
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const errData = await res.json();
      if (typeof errData.detail === "string") {
        detail = errData.detail;
      } else if (Array.isArray(errData.detail)) {
        detail = errData.detail.map((e: { msg: string }) => e.msg).join(". ");
      }
    } catch {
      // ignorar si no es JSON
    }
    throw new Error(detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export function getExportUrl(formato: "csv" | "xml"): string {
  return `${API_BASE}/admin/exportar?formato=${formato}`;
}