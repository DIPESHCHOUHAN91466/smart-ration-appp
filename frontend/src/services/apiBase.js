// Where the Python API lives. Set VITE_API_BASE_URL at build time for any deployment where the API
// is on another origin. Without it, development builds use the local API and production builds use
// same-origin "/api" (the reverse proxy in deployment/nginx) — never a hard-coded localhost.
// 127.0.0.1, not "localhost": the API binds IPv4 only, and "localhost" may resolve to IPv6 (::1) first,
// where another program (e.g. a Docker container publishing :8000) can answer instead.
export function resolveApiBaseUrl(configured, isDev) {
  return configured || (isDev ? "http://127.0.0.1:8000/api" : "/api");
}

// import.meta.env.DEV is replaced at build time, so production bundles don't contain the localhost URL.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? resolveApiBaseUrl("", true) : "/api");
