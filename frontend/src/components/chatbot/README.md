# src/components/chatbot — Ration Mitra AI Assistant (UI)

**What:** the reusable UI for the Public Help chatbot — floating button (bottom-right), chat window,
messages, quick questions, input. **Why:** one assistant, mounted once in `App.jsx`, on every page
except the full-screen QR scanner.
**Belongs here:** rendering and UI state only. **Doesn't:** business logic or knowledge — answers and
safety rules live on the server (`backend/SmartRation/app/ai/chatbot`, content in
`ai/chatbot/knowledge`); API communication lives in `services/chatbotService.js`.
**Run/test:** appears on http://localhost:5173; tests in `frontend/tests/unit/chatbot.test.jsx`.
**Connects:** `hooks/useChatbot.js` (conversation, kept in `sessionStorage`) → `services/chatbotService.js`
→ `POST /api/chatbot/message` on the Python API. Any page can open it with `openChatbot(question)`
from `state/chatbotStore.js`.

| File | Role |
|---|---|
| `ChatbotWidget.jsx` | launcher + window; unread badge, tooltip, Esc closes and returns focus |
| `ChatbotWindow.jsx` | header, conversation (search, typing indicator, empty and offline states), suggestions, input |
| `ChatbotHeader.jsx` | avatar, title, status; search, clear, expand, minimize, close |
| `ChatbotMessage.jsx` | a reply as paragraphs/lists (never HTML); in-app links only; related topics; error + retry |
| `ChatbotInput.jsx` | textarea (Enter sends, Shift+Enter new line, 500 characters), privacy hint, voice input button (🎤) |
| `ChatbotSuggestions.jsx` | quick-question chips (asked by topic id) |
| `ChatbotAvatar.jsx` | assistant avatar and launcher image: the official Ration Mitra logo (`src/assets/ration-mitra-logo.webp`, the same file as the headers), complete, in a round white badge |
| `ChatLanguageMenu.jsx`, `LanguageMenuItems.jsx`, `useMenu.js` | header 🌐 language menu, the shared English / हिन्दी / मराठी items, accessible popup-menu behaviour |
| `chatbot.css` | styles; bottom sheet on phones; reduced-motion aware |

**Voice input** (`hooks/useSpeechRecognition.js`): the browser's own Web Speech API
(`SpeechRecognition` / `webkitSpeechRecognition`) turns speech into text in the chat input — in the
app language (English `en-IN`, Hindi `hi-IN`, Marathi `mr-IN`). Words appear live; nothing is sent
until the user presses Send (Stop keeps the text for editing, Cancel/Esc restores what was typed).
The app never records or uploads audio and only receives text; note that some browsers (e.g. Chrome)
perform the recognition on their vendor's online speech service, so it needs a connection there.
Unsupported browsers, denied permission, no microphone, no speech, network and unsupported-language
errors each show a translated message. Sessions stop after 60 s, on language change and on close.
States: idle → requesting_permission → listening → processing → success (or error / unsupported).

Full design: [../../../../docs/chatbot/CHATBOT_ARCHITECTURE.md](../../../../docs/chatbot/CHATBOT_ARCHITECTURE.md).

**Launcher** (`ChatbotWidget.jsx`): a 72px white badge (68 tablet, 62 phone) with a thin blue ring, the
complete logo, a soft glow once every 7 s (off with prefers-reduced-motion), safe-area positioning and
z-index 150 (above pages, below dialogs). Click opens the chat. Long-press, right-click, Up arrow,
Shift+F10 or the ContextMenu key opens a compact menu: Voice input, English / हिन्दी / मराठी, Open chat.
First visit only: "Need help? Ask Ration Mitra AI" shows ~1.5 s after load for 5 s
(`localStorage.rationMitraTooltipSeen`). The chat header has **Voice input** and a **🌐 language** menu.
Language is the app-wide setting (`useLanguageStore`, persisted as `smart-ration-language`), so the chat,
the site and voice recognition always match. Voice from the header/menu goes through `pendingVoice` in
`state/chatbotStore.js` to the one voice implementation in `ChatbotInput`.

