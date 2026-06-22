import './CallControls.css'

/**
 * CallControls — phone-style bottom control bar.
 * Mute (left), End Call (center, red), Speaker (right).
 * When not in a call, the center button becomes "Start Call" (green).
 */
export function CallControls({ inCall, muted, onMute, onEndCall, onStartCall, onStartSpeaker, speakerOn }) {
  return (
    <div className="controls">
      <button
        className={`ctrl-btn ctrl-mute ${muted ? 'active' : ''}`}
        onClick={onMute}
        disabled={!inCall}
        aria-label={muted ? 'Unmute' : 'Mute'}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
          strokeLinecap="round" strokeLinejoin="round" width="22" height="22">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>
        {muted && (
          <span className="ctrl-strike">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" width="22" height="22">
              <line x1="4" y1="4" x2="20" y2="20" />
            </svg>
          </span>
        )}
        <span className="ctrl-label">Mute</span>
      </button>

      {inCall ? (
        <button className="ctrl-btn ctrl-end" onClick={onEndCall} aria-label="End call">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round" width="26" height="26"
            style={{ transform: 'rotate(135deg)' }}>
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </button>
      ) : (
        <button className="ctrl-btn ctrl-start" onClick={onStartCall} aria-label="Start call">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round" width="26" height="26">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </button>
      )}

      <button
        className={`ctrl-btn ctrl-speaker ${speakerOn && inCall ? 'active' : ''}`}
        onClick={onStartSpeaker}
        disabled={!inCall}
        aria-label="Speaker"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
          strokeLinecap="round" strokeLinejoin="round" width="22" height="22">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
        </svg>
        <span className="ctrl-label">Speaker</span>
      </button>
    </div>
  )
}