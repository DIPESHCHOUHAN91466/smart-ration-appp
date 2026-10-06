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

// The demo accounts' password, shown on the login page. PUBLIC by design (it is printed on screen): set it only for a
// synthetic-data demo, and only to the value the demo was seeded with (SEED_DEMO_PASSWORD). Unset: the demo buttons
// fill the email only and no password is shown — never a hard-coded guess in the bundle.
export const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || "";

// The developer status page (/status): development builds, or VITE_SHOW_STATUS=true.
export const SHOW_STATUS_PAGE = import.meta.env.DEV || import.meta.env.VITE_SHOW_STATUS === "true";
