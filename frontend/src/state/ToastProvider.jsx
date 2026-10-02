import { useCallback, useRef, useState } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { ToastContext } from "./toast";

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);

  const notify = useCallback((message, type = "success") => {
    setToast({ message, type });
    window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => setToast(null), 3500);
  }, []);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      {/* Always in the page, so screen readers announce what appears in it (WCAG 4.1.3): errors at once, others politely. */}
      <div className="toast-region" aria-live="polite" aria-atomic="true">
        {toast && (
          <div className={`toast ${toast.type === "error" ? "error" : ""}`} role={toast.type === "error" ? "alert" : "status"}>
            {toast.type === "error" ? <AlertCircle size={18} aria-hidden="true" /> : <CheckCircle2 size={18} aria-hidden="true" />}
            {toast.message}
          </div>
        )}
      </div>
    </ToastContext.Provider>
  );
}
