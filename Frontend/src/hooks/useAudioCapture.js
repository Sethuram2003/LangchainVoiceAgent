/** useAudioCapture — mic → 16kHz PCM s16le → onPcmChunk callback. */
import { useCallback, useRef, useState } from 'react'

const TARGET_RATE = 16000
const BUFFER_SIZE = 4096

function downsample(input, fromRate, toRate) {
  if (fromRate === toRate) return input
  const ratio = fromRate / toRate
  const len = Math.round(input.length / ratio)
  const out = new Float32Array(len)
  for (let i = 0; i < len; i++) {
    const s = Math.floor(i * ratio)
    const e = Math.min(Math.floor((i + 1) * ratio), input.length)
    let sum = 0
    for (let j = s; j < e; j++) sum += input[j]
    out[i] = sum / (e - s)
  }
  return out
}

function toPcm16(f32) {
  const buf = new ArrayBuffer(f32.length * 2)
  const dv = new DataView(buf)
  for (let i = 0; i < f32.length; i++) {
    let s = Math.max(-1, Math.min(1, f32[i]))
    s = s < 0 ? s * 0x8000 : s * 0x7fff
    dv.setInt16(i * 2, s, true)
  }
  return buf
}

export function useAudioCapture(onPcmChunk) {
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState(null)
  const ctxRef = useRef(null)
  const streamRef = useRef(null)
  const nodeRef = useRef(null)
  const cbRef = useRef(onPcmChunk)
  cbRef.current = onPcmChunk

  const start = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      })
      streamRef.current = stream
      const ctx = new AudioContext()
      ctxRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const node = ctx.createScriptProcessor(BUFFER_SIZE, 1, 1)
      nodeRef.current = node
      node.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)
        const ds = downsample(input, ctx.sampleRate, TARGET_RATE)
        const pcm = toPcm16(ds)
        if (cbRef.current) cbRef.current(pcm)
      }
      source.connect(node)
      node.connect(ctx.destination)
      setIsCapturing(true)
    } catch (e) {
      setError(e.message || 'Microphone access denied')
    }
  }, [])

  const stop = useCallback(() => {
    if (nodeRef.current) { nodeRef.current.disconnect(); nodeRef.current = null }
    if (streamRef.current) { streamRef.current.getTracks().forEach((t) => t.stop()); streamRef.current = null }
    if (ctxRef.current) { ctxRef.current.close(); ctxRef.current = null }
    setIsCapturing(false)
  }, [])

  return { start, stop, isCapturing, error }
}