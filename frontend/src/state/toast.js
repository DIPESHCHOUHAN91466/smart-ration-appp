import { createContext, useContext } from "react";

// App-wide notifications ("Booking confirmed", "Could not load…"). The provider that renders them is
// ToastProvider.jsx; components only need this hook:  const notify = useToast(); notify(msg, "error").
export const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
