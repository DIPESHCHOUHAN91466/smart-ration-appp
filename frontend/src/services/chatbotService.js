import { apiClient } from "./api";

// Public Help assistant (Python backend, no login needed). See docs/CHATBOT.md.
export const chatbotService = {
  welcome: (language) => apiClient.get("/chatbot/welcome", { params: { language } }).then((r) => r.data.data),

  /** One of: { message } | { topic } (quick button) | { articleId } (related topic). */
  send: ({ message, topic, articleId, language }) =>
    apiClient.post("/chatbot/message", { message, topic, articleId, language }).then((r) => r.data.data),
};

export const publicHelpService = {
  categories: (language) => apiClient.get("/public-help/categories", { params: { language } }).then((r) => r.data.data),
  article: (id, language) => apiClient.get(`/public-help/articles/${encodeURIComponent(id)}`, { params: { language } }).then((r) => r.data.data),
  search: (q, language) => apiClient.get("/public-help/search", { params: { q, language } }).then((r) => r.data.data),
};
