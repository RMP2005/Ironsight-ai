type AppHeaderProps = {
  isOnline: boolean;
};

export function AppHeader({ isOnline }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          IS
        </span>
        <div>
          <p className="eyebrow">IronSight AI</p>
          <p className="brand-subtitle">Predictive Maintenance Decision Support</p>
        </div>
      </div>
      <div
        className={`system-status ${isOnline ? "system-ready" : "system-offline"}`}
        role="status"
        aria-live="polite"
      >
        <span aria-hidden="true">●</span>
        System {isOnline ? "Ready" : "Offline"}
      </div>
    </header>
  );
}
