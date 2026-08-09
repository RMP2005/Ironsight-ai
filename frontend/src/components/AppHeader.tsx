type AppHeaderProps = {
  isOnline: boolean;
};

import { IronSightEmblem } from "@/components/IronSightEmblem";

export function AppHeader({ isOnline }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-emblem-wrap" aria-hidden="true">
          <IronSightEmblem className="brand-emblem" />
        </span>
        <div className="brand-copy">
          <p className="brand-wordmark">IronSight AI</p>
          <p className="brand-subtitle">Predictive Maintenance Decision Support</p>
        </div>
      </div>
      <div
        className={`system-status ${isOnline ? "system-ready" : "system-offline"}`}
        role="status"
        aria-live="polite"
      >
        <span className="status-dot" aria-hidden="true" />
        System {isOnline ? "Ready" : "Offline"}
      </div>
    </header>
  );
}
