// Every build-time setting the browser app reads, in one place. Vite inlines import.meta.env when it
// builds, so these are constants in the bundle — and anything named VITE_* is PUBLIC: never put a secret
// in one. Documented in frontend/.env.example.
import { withApiVersion } from "../api/baseUrl";

export const IS_DEV = import.meta.env.DEV;

// The Python API (see api/baseUrl.js for the rules): same origin unless VITE_API_BASE_URL says otherwise.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? withApiVersion(import.meta.env.VITE_API_BASE_URL)
  : "/api/v1";   // Vite proxies /api in development (vite.config.js)

// The login page offers the synthetic demo accounts unless the build sets VITE_DEMO_MODE=false.
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE !== "false";

// The developer status page (/status): development builds, or VITE_SHOW_STATUS=true.
export const SHOW_STATUS_PAGE = import.meta.env.DEV || import.meta.env.VITE_SHOW_STATUS === "true";
