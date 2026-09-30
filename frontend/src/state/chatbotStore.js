import { create } from "zustand";

// Lets any page open the Public Help assistant, optionally with a question to ask
// (e.g. "Ask the assistant" on the help page). The widget itself is mounted once in App.
// `pendingVoice`: voice input was requested (header 🎤 or the launcher menu); the chat input starts
// listening as soon as it is mounted and clears the flag — one voice implementation, in ChatbotInput.
export const useChatbotStore = create((set) => ({
  isOpen: false,
  pendingQuestion: null,
  pendingVoice: false,
  open: (question = null) => set({ isOpen: true, pendingQuestion: question }),
  close: () => set({ isOpen: false }),
  takePendingQuestion: () => {
    let question = null;
    set((state) => {
      question = state.pendingQuestion;
      return { pendingQuestion: null };
    });
    return question;
  },
  requestVoice: () => set({ isOpen: true, pendingVoice: true }),
  consumeVoice: () => set({ pendingVoice: false }),
}));

export const openChatbot = (question) => useChatbotStore.getState().open(question);
