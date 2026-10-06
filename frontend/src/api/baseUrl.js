// Where the Python API lives. Default: same-origin "/api/v1" — in production the API serves the website (or
// the reverse proxy in deployment/nginx), in development Vite proxies /api to 127.0.0.1:8000 (vite.config.js).
// Same origin is required for the HttpOnly session cookie (SameSite=Strict). VITE_API_BASE_URL can still point
// elsewhere, but then sessions end after 15 minutes (the cookie isn't sent to another site).
//
// The app calls the versioned API (/api/v1). A base that ends in a bare "/api" (older .env files) gets
// "/v1" added, so existing configurations switch over without being edited; /api keeps working too.
export const API_VERSION = "v1";

export function withApiVersion(base) {
  const trimmed = base.replace(/\/+$/, "");
  return /\/api$/.test(trimmed) ? `${trimmed}/${API_VERSION}` : trimmed;
}

export function resolveApiBaseUrl(configured) {
  return withApiVersion(configured || "/api");
}

// The value the app uses is config/env.js API_BASE_URL (built with these rules from VITE_API_BASE_URL).
