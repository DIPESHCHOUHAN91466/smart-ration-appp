// Shapes of the data the API sends, as JSDoc types. The app is plain JavaScript; these give editors
// (VS Code IntelliSense, "Go to type") and reviewers one place that states the contract, matching
// docs/api/openapi/python-api.openapi.json and the C# DTOs. Import a type in a comment:
//   /** @param {import("../types/api").UserSummary} user */
// This module has no runtime code.

/**
 * Every response from both backends: { success, message, data, errors, errorCode }.
 * @template T
 * @typedef {object} ApiEnvelope
 * @property {boolean} success
 * @property {string} message
 * @property {T | null} data
 * @property {string[] | null} errors      validation messages, one per problem
 * @property {string} [errorCode]          machine-readable, e.g. "PAYLOAD_TOO_LARGE"
 */

/**
 * What api/client.js rejects with: the envelope's message, never a raw Axios error.
 * @typedef {Error & { status?: number, errors: string[] | null }} ApiError
 */

/** @typedef {"RuralUser" | "ShopOwner" | "GovernmentOfficial" | "Admin"} UserRole */

/**
 * @typedef {object} UserSummary
 * @property {number} id
 * @property {string} fullName
 * @property {string} email
 * @property {string} mobileNumber
 * @property {UserRole} role
 * @property {number | null} rationShopId   set for shop owners only
 */

/**
 * POST /auth/login, /auth/register, /auth/refresh.
 * @typedef {object} AuthResponse
 * @property {string} accessToken            JWT, 15 minutes
 * @property {string} refreshToken           rotated on every refresh
 * @property {string} accessTokenExpiresAt   ISO-8601 UTC
 * @property {UserSummary} user
 */

/** @typedef {"Pending" | "Confirmed" | "Completed" | "Cancelled" | "NoShow"} TokenStatus */

/** @typedef {"Rice" | "Wheat" | "Sugar" | "Pulses" | "EdibleOil" | "Salt"} RationType */

export {};
