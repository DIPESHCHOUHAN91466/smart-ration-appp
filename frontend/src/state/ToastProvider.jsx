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
      {toast && (
        <div className={`toast ${toast.type === "error" ? "error" : ""}`}>
          {toast.type === "error" ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          {toast.message}
        </div>
      )}
    </ToastContext.Provider>
  );
}
