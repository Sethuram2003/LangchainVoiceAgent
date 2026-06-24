/** useAudioPlayback — seamless PCM s16le playback via Web Audio API.
 * The sample rate is provided per-chunk by the backend (Cartesia=24000,
 * Miso=variable). We recreate the AudioContext if the rate changes.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

function b64ToF32(b64) {
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  const n = bytes.length / 2
  const f32 = new Float32Array(n)
  const dv = new DataView(bytes.buffer)
  for (let i = 0; i < n; i++) f32[i] = dv.getInt16(i * 2, true) / 32768
  return f32
}

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false)
  const ctxRef = useRef(null)
  const currentRateRef = useRef(0)
  const nextTimeRef = useRef(0)
  const activeRef = useRef(0)

  const ensureCtx = useCallback((sampleRate) => {
    // Recreate context if sample rate changed (e.g. switching TTS providers).
    if (ctxRef.current && currentRateRef.current !== sampleRate) {
      try { ctxRef.current.close() } catch {}
      ctxRef.current = null
    }
    if (!ctxRef.current) {
      ctxRef.current = new AudioContext({ sampleRate })
      currentRateRef.current = sampleRate
    }
    if (ctxRef.current.state === 'suspended') ctxRef.current.resume()
    return ctxRef.current
  }, [])

  const play = useCallback((b64, sampleRate = 24000) => {
    if (!b64) return
    const ctx = ensureCtx(sampleRate)
    const f32 = b64ToF32(b64)
    const buf = ctx.createBuffer(1, f32.length, sampleRate)
    buf.copyToChannel(f32, 0)
    const src = ctx.createBufferSource()
    src.buffer = buf
    src.connect(ctx.destination)
    const now = ctx.currentTime
    if (nextTimeRef.current < now) nextTimeRef.current = now
    src.start(nextTimeRef.current)
    nextTimeRef.current += buf.duration
    activeRef.current += 1
    setIsPlaying(true)
    src.onended = () => {
      activeRef.current -= 1
      if (activeRef.current <= 0) { activeRef.current = 0; setIsPlaying(false) }
    }
  }, [ensureCtx])

  const stop = useCallback(() => {
    if (ctxRef.current) { ctxRef.current.close(); ctxRef.current = null }
    nextTimeRef.current = 0
    activeRef.current = 0
    currentRateRef.current = 0
    setIsPlaying(false)
  }, [])

  useEffect(() => () => { if (ctxRef.current) ctxRef.current.close() }, [])

  return { play, stop, isPlaying }
}