const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

export async function api(path, options = {}) {
  const bases = [API_BASE, buildFallbackBase(API_BASE)].filter(Boolean);
  let response = null;

  for (const base of bases) {
    try {
      response = await fetch(`${base}${path}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(options.headers ?? {})
        },
        ...options
      });
      if (response) {
        break;
      }
    } catch (error) {
      // try next base
    }
  }

  if (!response) {
    throw new Error("Network error: backend unavailable or CORS blocked. Open app via http://localhost:5173.");
  }

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function buildFallbackBase(base) {
  try {
    const url = new URL(base);
    if (url.hostname === "localhost") {
      url.hostname = "127.0.0.1";
      return url.toString().replace(/\/$/, "");
    }
    if (url.hostname === "127.0.0.1") {
      url.hostname = "localhost";
      return url.toString().replace(/\/$/, "");
    }
  } catch {
    return null;
  }
  return null;
}

export { API_BASE };
