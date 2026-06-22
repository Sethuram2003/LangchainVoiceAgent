/**
 * useWebSocket — manages the WebSocket connection to the voice agent backend.
 *
 * Protocol: audio bytes in, JSON events out. Events:
 *   - stt_chunk / stt_output: transcript (with speaker label)
 *   - agent_chunk / agent_end: streamed LLM text
 *   - tts_chunk: base64-encoded PCM audio
 *
 * Returns: { status, send, onEvent, close }
 */
import { useCallback, useEffect, useRef, useState } from 'react'

export function useWebSocket(url) {
  const [status, setStatus] = useState('idle')
  const wsRef = useRef(null)
  const handlersRef = useRef(new Set())

  const onEvent = useCallback((handler) => {
    handlersRef.current.add(handler)
    return () => handlersRef.current.delete(handler)
  }, [])

  const send = useCallback((bytes) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(bytes)
  }, [])

  const close = useCallback(() => {
    const ws = wsRef.current
    if (ws) {
      try { ws.close() } catch {}
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!url) return
    setStatus('connecting')
    const ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => setStatus('open')
    ws.onclose = () => setStatus('closed')
    ws.onerror = () => setStatus('error')
    ws.onmessage = (msg) => {
      const text = typeof msg.data === 'string' ? msg.data : ''
      if (!text) return
      try {
        const event = JSON.parse(text)
        handlersRef.current.forEach((h) => h(event))
      } catch {}
    }

    return () => {
      try { ws.close() } catch {}
      wsRef.current = null
    }
  }, [url])

  return { status, send, onEvent, close }
}