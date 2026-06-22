import './StatusBar.css'
import { phaseLabel } from '../utils/format'

/** StatusBar — iOS-style top bar with time, phase label, and settings cog. */
export function StatusBar({ phase, wsStatus, onSettings }) {
  const time = new Date().toLocaleTimeString([], {
    hour: '2-digit', minute: '2-digit', hour12: false,
  })

  const dotClass =
    wsStatus === 'open' ? (phase === 'idle' ? 'ready' : 'live') :
    wsStatus === 'connecting' ? 'wait' :
    wsStatus === 'error' ? 'err' : 'off'

  return (
    <div className="statusbar">
      <span className="sb-time">{time}</span>
      <div className="sb-center">
        <span className={`sb-dot sb-dot--${dotClass}`} />
        <span className="sb-label">{phaseLabel(phase, wsStatus)}</span>
      </div>
      <button className="sb-gear" onClick={onSettings} aria-label="Settings">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
          strokeLinecap="round" strokeLinejoin="round" width="19" height="19">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>
    </div>
  )
}