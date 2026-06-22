/**
 * useCallState — tracks the call phase from event flow.
 *   idle → connecting → listening → agent_thinking → agent_speaking → listening ...
 */
import { useEffect, useReducer, useRef } from 'react'

const RESET_MS = 800

export function useCallState(wsStatus) {
  const [state, dispatch] = useReducer((s, action) => {
    switch (action.type) {
      case 'ws': return { phase: action.status === 'open' ? 'idle' : 'connecting' }
      case 'stt_chunk':
        if (['idle', 'agent_speaking', 'connecting'].includes(s.phase)) return { phase: 'listening' }
        return s
      case 'stt_output': return { phase: 'agent_thinking' }
      case 'agent_chunk': return { phase: 'agent_speaking' }
      case 'reset': return s.phase === 'agent_speaking' ? { phase: 'listening' } : s
      default: return s
    }
  }, { phase: 'idle' })

  const timerRef = useRef(null)

  // When agent starts speaking, schedule a reset to listening after TTS finishes.
  useEffect(() => {
    if (state.phase === 'agent_speaking') {
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => dispatch({ type: 'reset' }), RESET_MS)
    }
    return () => { if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null } }
  }, [state.phase])

  // Sync with WebSocket status.
  useEffect(() => { dispatch({ type: 'ws', status: wsStatus }) }, [wsStatus])

  return { phase: state.phase, dispatch }
}