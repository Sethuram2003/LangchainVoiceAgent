import './AgentAvatar.css'

/**
 * AgentAvatar — animated circular avatar reflecting the agent's phase.
 * idle: breathing dot. listening: expanding rings. thinking: bouncing dots.
 * speaking: animated waveform bars.
 */
export function AgentAvatar({ phase }) {
  return (
    <div className={`avatar avatar--${phase}`}>
      <div className="av-rings">
        <span className="av-ring r1" />
        <span className="av-ring r2" />
        <span className="av-ring r3" />
      </div>
      <div className="av-core">
        {phase === 'agent_speaking' ? (
          <div className="av-wave">
            <span /><span /><span /><span /><span />
          </div>
        ) : phase === 'agent_thinking' ? (
          <div className="av-dots">
            <span /><span /><span />
          </div>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            width="28" height="28">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        )}
      </div>
    </div>
  )
}