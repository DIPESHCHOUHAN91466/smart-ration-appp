// Where the Python API lives. Set VITE_API_BASE_URL at build time for any deployment where the API
// is on another origin. Without it, development builds use the local API and production builds use
// same-origin "/api/v1" (the reverse proxy in deployment/nginx) — never a hard-coded localhost.
// 127.0.0.1, not "localhost": the API binds IPv4 only, and "localhost" may resolve to IPv6 (::1) first,
// where another program (e.g. a Docker container publishing :8000) can answer instead.
//
// The app calls the versioned API (/api/v1). A base that ends in a bare "/api" (older .env files) gets
// "/v1" added, so existing configurations switch over without being edited; /api keeps working too.
export const API_VERSION = "v1";

export function withApiVersion(base) {
  const trimmed = base.replace(/\/+$/, "");
  return /\/api$/.test(trimmed) ? `${trimmed}/${API_VERSION}` : trimmed;
}

export function resolveApiBaseUrl(configured, isDev) {
  return withApiVersion(configured || (isDev ? "http://127.0.0.1:8000/api" : "/api"));
}

// The value the app uses is config/env.js API_BASE_URL (built with these rules from VITE_API_BASE_URL).
