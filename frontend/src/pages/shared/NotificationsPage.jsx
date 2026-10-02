import { useEffect, useState } from "react";
import { Bell, CheckCircle2 } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getNotifications, markNotificationsRead } from "../../services/notificationsService";
import { useToast } from "../../state/toast";
import { useTranslation } from "../../i18n/useTranslation";
import { formatDateTime } from "../../utils/format";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState(null);
  const [error, setError] = useState("");
  const notify = useToast();
  const { language } = useTranslation();

  const load = () => {
    setError("");
    setNotifications(null);
    getNotifications()
      .then(setNotifications)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const markRead = async (id) => {
    try {
      await markNotificationsRead([id]);
      setNotifications((items) => items.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
    } catch (err) {
      notify(err.message || "Could not mark as read", "error");
    }
  };

  const markAllRead = async () => {
    const unreadIds = (notifications || []).filter((n) => !n.isRead).map((n) => n.id);
    if (unreadIds.length === 0) return;
    try {
      await markNotificationsRead(unreadIds);
      setNotifications((items) => items.map((n) => ({ ...n, isRead: true })));
      notify("All notifications marked as read");
    } catch (err) {
      notify(err.message || "Could not mark all as read", "error");
    }
  };

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle="Updates about your bookings, collections and account."
        action={
          notifications?.some((n) => !n.isRead) && (
            <button className="secondary-btn" onClick={markAllRead}>
              <CheckCircle2 size={16} /> Mark all read
            </button>
          )
        }
      />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && notifications === null && <LoadingState text="Loading notifications..." />}
        {!error && notifications?.length === 0 && (
          <EmptyState title="No notifications yet" text="You'll see booking, collection and stock updates here." />
        )}
        {!error &&
          notifications?.length > 0 &&
          notifications.map((n) => (
            // Unread items are tinted; read ones stay at full contrast (fading them made the text unreadable, WCAG 1.4.3).
            <div className="complaint" key={n.id} style={n.isRead ? undefined : { background: "#eef5ff", borderRadius: 10, paddingInline: 10 }}>
              <Bell size={18} />
              <div>
                <b>{n.title}</b>
                <small>
                  {n.message} • {formatDateTime(n.createdAt, language)}
                </small>
              </div>
              {!n.isRead && (
                <button className="secondary-btn" onClick={() => markRead(n.id)}>
                  Mark read
                </button>
              )}
            </div>
          ))}
      </section>
    </>
  );
}
