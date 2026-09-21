import { ClipboardList, AlertCircle } from "lucide-react";

export function EmptyState({ title, text }) {
  return (
    <div className="empty">
      <ClipboardList size={42} />
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", text, onRetry }) {
  return (
    <div className="empty">
      <AlertCircle size={42} />
      <h2>{title}</h2>
      <p>{text}</p>
      {onRetry && (
        <button className="secondary-btn" style={{ marginTop: 14 }} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function LoadingState({ text = "Loading..." }) {
  return (
    <div className="empty">
      <p>{text}</p>
    </div>
  );
}
