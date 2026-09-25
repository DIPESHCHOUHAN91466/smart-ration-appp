# Public Help chatbot (frontend)

| File | Role |
|---|---|
| `ChatbotWidget.jsx` | Floating launcher (bottom-right) + window; unread badge, tooltip, Esc to close. Mounted once in `App.jsx`. |
| `ChatbotWindow.jsx` | Header, conversation (search, typing indicator, empty state), suggestions, input. |
| `ChatbotHeader.jsx` | Avatar, title, online status; search, clear, expand, minimize, close. |
| `ChatbotMessage.jsx` | Renders a reply as paragraphs/lists (never HTML); in-app links only; related topics; error + retry. |
| `ChatbotInput.jsx` | Textarea (Enter sends, Shift+Enter new line, 500 characters), privacy hint. |
| `ChatbotSuggestions.jsx` | Quick-question chips (asked by topic id, so answers are exact). |
| `ChatbotAvatar.jsx` | Assistant avatar (`src/assets/chatbot/`). |
| `chatbot.css` | Styles; bottom sheet on phones; reduced-motion aware. |

State: `hooks/useChatbot.js` (conversation in `sessionStorage`), `store/chatbotStore.js`
(`openChatbot(question)` from any page). API: `services/chatbotService.js` → Python
`/api/chatbot/*`. Knowledge and safety rules live on the server — see `docs/CHATBOT.md`.
