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

**Voice input** (`hooks/useSpeechRecognition.js`): the browser's own Web Speech API
(`SpeechRecognition` / `webkitSpeechRecognition`) turns speech into text in the chat input — in the
app language (English `en-IN`, Hindi `hi-IN`, Marathi `mr-IN`). Words appear live; nothing is sent
until the user presses Send (Stop keeps the text for editing, Cancel/Esc restores what was typed).
The app never records or uploads audio and only receives text; note that some browsers (e.g. Chrome)
perform the recognition on their vendor's online speech service, so it needs a connection there.
Unsupported browsers, denied permission, no microphone, no speech, network and unsupported-language
errors each show a translated message. Sessions stop after 60 s, on language change and on close.
| `ChatbotSuggestions.jsx` | quick-question chips (asked by topic id) |
| `ChatbotAvatar.jsx` | assistant avatar and launcher image: the Ration Mitra emblem (`src/assets/ration-mitra-emblem.png`, Logo 2) |
| `chatbot.css` | styles; bottom sheet on phones; reduced-motion aware |

Full design: [../../../../docs/chatbot/CHATBOT_ARCHITECTURE.md](../../../../docs/chatbot/CHATBOT_ARCHITECTURE.md).
