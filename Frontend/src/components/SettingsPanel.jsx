import './SettingsPanel.css'

/** SettingsPanel — slide-down overlay for backend URL configuration. */
export function SettingsPanel({ open, onClose, backendUrl, onBackendUrlChange }) {
  return (
    <>
      <div
        className={`settings-overlay ${open ? 'show' : ''}`}
        onClick={onClose}
      />
      <div className={`settings-panel ${open ? 'open' : ''}`}>
        <div className="settings-handle" />
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="settings-close" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" width="18" height="18">
              <line x1="6" y1="6" x2="18" y2="18" />
              <line x1="18" y1="6" x2="6" y2="18" />
            </svg>
          </button>
        </div>
        <div className="settings-body">
          <label className="settings-field">
            <span className="settings-label">Backend WebSocket URL</span>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => onBackendUrlChange(e.target.value)}
              placeholder="ws://localhost:8000/ws"
            />
          </label>
          <p className="settings-hint">
            The frontend connects to this URL for streaming audio and receiving events.
            Use <code>ws://localhost:8000/ws</code> for local development.
          </p>
        </div>
      </div>
    </>
  )
}