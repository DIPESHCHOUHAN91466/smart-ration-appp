import { useCallback, useEffect, useRef, useState } from "react";
import { chatbotService } from "../services/chatbotService";

// Conversation state for the Public Help assistant.
// History lives in sessionStorage only: it survives navigation but is gone when the tab closes
// (shared phones), and it never leaves the browser except as the next question.
const STORAGE_KEY = "smart-ration-chat";
const MAX_STORED = 60;

let nextId = 0;
const newId = () => `m${Date.now().toString(36)}${(nextId++).toString(36)}`;

function load() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(saved) ? saved.filter((m) => m && typeof m.text === "string" && (m.role === "user" || m.role === "bot")) : [];
  } catch {
    return [];
  }
}

function save(messages) {
  try {
    const persistent = messages.filter((m) => !m.error).slice(-MAX_STORED);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persistent));
  } catch {
    /* storage full or blocked: keep the conversation in memory only */
  }
}

function botMessage(reply) {
  return {
    id: newId(), role: "bot", text: reply.text, kind: reply.kind, title: reply.title, links: reply.links || [],
    related: reply.related || [], suggestions: reply.suggestions || [], requiresLogin: !!reply.requiresLogin, at: Date.now(),
  };
}

export function useChatbot(language) {
  const [messages, setMessages] = useState(load);
  const [pending, setPending] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const lastRequest = useRef(null);
  const onBotMessage = useRef(null);

  useEffect(() => save(messages), [messages]);

  const loadWelcome = useCallback(async () => {
    try {
      const reply = await chatbotService.welcome(language);
      setSuggestions(reply.suggestions || []);
      setMessages((current) => (current.length ? current : [botMessage(reply)]));
    } catch {
      setSuggestions([]);
    }
  }, [language]);

  const ask = useCallback(async (request) => {
    const payload = { ...request, language };
    lastRequest.current = payload;
    setPending(true);
    setMessages((current) => current.filter((m) => !m.error));
    try {
      const reply = await chatbotService.send(payload);
      const message = botMessage(reply);
      setMessages((current) => [...current, message]);
      if (reply.suggestions?.length) setSuggestions(reply.suggestions);
      onBotMessage.current?.(message);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { id: newId(), role: "bot", error: error.status === 429 ? "rate_limited" : "unavailable", text: "", at: Date.now() },
      ]);
    } finally {
      setPending(false);
    }
  }, [language]);

  const send = useCallback((text) => {
    const message = text.trim();
    if (!message || pending) return;
    setMessages((current) => [...current, { id: newId(), role: "user", text: message, at: Date.now() }]);
    ask({ message });
  }, [ask, pending]);

  /** A quick button or related topic: shows the label as the user's message, asks by id. */
  const choose = useCallback(({ label, topic, articleId }) => {
    if (pending) return;
    setMessages((current) => [...current, { id: newId(), role: "user", text: label, at: Date.now() }]);
    ask(topic ? { topic } : { articleId });
  }, [ask, pending]);

  const retry = useCallback(() => {
    if (lastRequest.current && !pending) ask(lastRequest.current);
  }, [ask, pending]);

  const clear = useCallback(() => {
    setMessages([]);
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    loadWelcome();
  }, [loadWelcome]);

  return { messages, pending, suggestions, send, choose, retry, clear, loadWelcome, onBotMessage };
}
