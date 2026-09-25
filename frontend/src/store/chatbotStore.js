import { create } from "zustand";

// Lets any page open the Public Help assistant, optionally with a question to ask
// (e.g. "Ask the assistant" on the help page). The widget itself is mounted once in App.
export const useChatbotStore = create((set) => ({
  isOpen: false,
  pendingQuestion: null,
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
}));

export const openChatbot = (question) => useChatbotStore.getState().open(question);
