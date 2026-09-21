const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5188/api";

/**
 * Common API request helper.
 *
 * React components should call functions from this service
 * instead of directly using fetch() everywhere.
 */
export async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      errorText || `API request failed with status ${response.status}`,
    );
  }

  // Some DELETE/204 responses may have no body.
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * GET request
 */
export function get(endpoint) {
  return request(endpoint);
}

/**
 * POST request
 */
export function post(endpoint, data) {
  return request(endpoint, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * PUT request
 */
export function put(endpoint, data) {
  return request(endpoint, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * DELETE request
 */
export function remove(endpoint) {
  return request(endpoint, {
    method: "DELETE",
  });
}

export default {
  request,
  get,
  post,
  put,
  remove,
};
