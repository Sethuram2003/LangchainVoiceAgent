/** Small helpers used across components. */

/** Format ms timestamp as HH:MM. */
export function fmtTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/** Speaker label → CSS color var. */
export function speakerColor(label) {
  switch (label) {
    case 'A': return 'var(--sp-a)'
    case 'B': return 'var(--sp-b)'
    case 'C': return 'var(--sp-c)'
    case 'D': return 'var(--sp-d)'
    default: return 'var(--sp-x)'
  }
}

/** Speaker label → CSS background var. */
export function speakerBg(label) {
  switch (label) {
    case 'A': return 'var(--sp-a-bg)'
    case 'B': return 'var(--sp-b-bg)'
    case 'C': return 'var(--sp-c-bg)'
    case 'D': return 'var(--sp-d-bg)'
    default: return 'var(--sp-x-bg)'
  }
}

/** Short phase label for the status bar. */
export function phaseLabel(phase, wsStatus) {
  if (wsStatus !== 'open') {
    if (wsStatus === 'connecting') return 'Connecting'
    if (wsStatus === 'error') return 'Error'
    return 'Offline'
  }
  switch (phase) {
    case 'idle': return 'Ready'
    case 'listening': return 'Listening'
    case 'agent_thinking': return 'Thinking'
    case 'agent_speaking': return 'Speaking'
    case 'connecting': return 'Connecting'
    default: return 'Ready'
  }
}