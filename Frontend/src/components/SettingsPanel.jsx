import './SettingsPanel.css'

/**
 * SettingsPanel — slide-down overlay for backend URL and TTS provider config.
 */
export function SettingsPanel({
  open,
  onClose,
  backendUrl,
  onBackendUrlChange,
  ttsProvider,
  onTtsProviderChange,
}) {
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
          {/* TTS Provider Selector */}
          <div className="settings-field">
            <span className="settings-label">TTS Provider</span>
            <div className="tts-toggle">
              <button
                className={`tts-option ${ttsProvider === 'cartesia' ? 'active' : ''}`}
                onClick={() => onTtsProviderChange('cartesia')}
              >
                <div className="tts-option-header">
                  <span className="tts-option-name">Cartesia</span>
                  {ttsProvider === 'cartesia' && (
                    <span className="tts-check">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                        width="14" height="14">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </span>
                  )}
                </div>
                <span className="tts-option-desc">Cloud streaming, low latency</span>
              </button>
              <button
                className={`tts-option ${ttsProvider === 'kokoro' ? 'active' : ''}`}
                onClick={() => onTtsProviderChange('kokoro')}
              >
                <div className="tts-option-header">
                  <span className="tts-option-name">kokoro One</span>
                  {ttsProvider === 'kokoro' && (
                    <span className="tts-check">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                        width="14" height="14">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </span>
                  )}
                </div>
                <span className="tts-option-desc">Local inference, no API key</span>
              </button>
            </div>
          </div>

          {/* Backend URL */}
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
            The TTS provider is sent as a <code>?tts=</code> query parameter.
          </p>
        </div>
      </div>
    </>
  )
}