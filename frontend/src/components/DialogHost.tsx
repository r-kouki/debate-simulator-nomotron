import { useDialogStore } from "../state/dialogStore";

const DialogHost = () => {
  const { dialogs, closeDialog } = useDialogStore();

  if (dialogs.length === 0) {
    return null;
  }

  return (
    <div className="dialog-overlay" role="presentation">
      {dialogs.map((dialog) => (
        <div
          key={dialog.id}
          className="window"
          role="dialog"
          aria-modal="true"
          aria-label={dialog.title}
        >
          <div className="title-bar">
            <div className="title-bar-text">{dialog.title}</div>
            <div className="title-bar-controls">
              <button
                aria-label="Close"
                onClick={() => closeDialog(dialog.id)}
                type="button"
              />
            </div>
          </div>
          <div className="window-body">
            <p>{dialog.message}</p>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              {dialog.actions.map((action) => (
              <button
                key={action.label}
                type="button"
                onClick={() => {
                  action.onClick();
                  closeDialog(dialog.id);
                }}
              >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DialogHost;
