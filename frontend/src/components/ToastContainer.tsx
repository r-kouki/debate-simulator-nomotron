import { useEffect } from "react";
import { useNotificationStore } from "../state/notificationStore";

const AUTO_DISMISS_MS = 5000;

const ToastContainer = () => {
  const { notifications, remove } = useNotificationStore();

  useEffect(() => {
    if (notifications.length === 0) {
      return;
    }
    const timers = notifications.map((note) =>
      window.setTimeout(() => remove(note.id), AUTO_DISMISS_MS)
    );
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [notifications, remove]);

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="toast-container" aria-live="polite">
      {notifications.map((note) => (
        <div key={note.id} className="toast" role="status">
          <strong>{note.title}</strong>
          <div>{note.message}</div>
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;
