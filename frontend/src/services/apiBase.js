// Where the Python API lives. Set VITE_API_BASE_URL at build time for any deployment where the API
// is on another origin. Without it, development builds use the local API and production builds use
// same-origin "/api" (the reverse proxy in deployment/nginx) — never a hard-coded localhost.
export function resolveApiBaseUrl(configured, isDev) {
  return configured || (isDev ? "http://localhost:8000/api" : "/api");
}

// import.meta.env.DEV is replaced at build time, so production bundles don't contain the localhost URL.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? resolveApiBaseUrl("", true) : "/api");
