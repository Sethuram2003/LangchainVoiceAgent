import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import { PhoneFrame } from './components/PhoneFrame'
import { StatusBar } from './components/StatusBar'
import { AgentAvatar } from './components/AgentAvatar'
import { ConversationList } from './components/ConversationList'
import { LiveTranscript } from './components/LiveTranscript'
import { CallControls } from './components/CallControls'
import { SettingsPanel } from './components/SettingsPanel'
import { useWebSocket } from './hooks/useWebSocket'
import { useAudioCapture } from './hooks/useAudioCapture'
import { useAudioPlayback } from './hooks/useAudioPlayback'
import { useCallState } from './hooks/useCallState'

let msgId = 0

export default function App() {
  const [backendUrl, setBackendUrl] = useState('ws://localhost:8000/ws')
  const [ttsProvider, setTtsProvider] = useState('cartesia')
  const [wsUrl, setWsUrl] = useState(null)
  const [inCall, setInCall] = useState(false)
  const [muted, setMuted] = useState(false)
  const [speakerOn, setSpeakerOn] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [partial, setPartial] = useState('')
  const [partialSpeaker, setPartialSpeaker] = useState('')
  const [agentText, setAgentText] = useState('')

  // Accumulate agent chunks so we can add the full text to conversation.
  const agentBufRef = useRef('')

  const { status: wsStatus, send, onEvent, close } = useWebSocket(wsUrl)
  const { phase, dispatch } = useCallState(wsStatus)
  const { play, stop: stopPlayback, isPlaying } = useAudioPlayback()

  // Audio capture — send PCM to backend when capturing and not muted.
  const handlePcm = useCallback((pcm) => {
    if (!muted) send(pcm)
  }, [muted, send])

  const { start: startMic, stop: stopMic, isCapturing, error: micError } =
    useAudioCapture(handlePcm)

  // Subscribe to backend events.
  useEffect(() => {
    if (!wsUrl) return
    const unsub = onEvent((event) => {
      switch (event.type) {
        case 'stt_chunk':
          setPartial(event.transcript || '')
          setPartialSpeaker(event.speaker || 'UNKNOWN')
          dispatch({ type: 'stt_chunk' })
          break
        case 'stt_output':
          setPartial('')
          setMessages((prev) => [
            ...prev,
            {
              id: ++msgId,
              role: 'user',
              text: event.transcript,
              speaker: event.speaker || 'UNKNOWN',
              ts: event.ts,
            },
          ])
          setAgentText('')
          agentBufRef.current = ''
          dispatch({ type: 'stt_output' })
          break
        case 'agent_chunk':
          agentBufRef.current += event.text
          setAgentText(agentBufRef.current)
          dispatch({ type: 'agent_chunk' })
          break
        case 'agent_end':
          setMessages((prev) => [
            ...prev,
            {
              id: ++msgId,
              role: 'agent',
              text: event.text,
              ts: event.ts,
            },
          ])
          setAgentText('')
          agentBufRef.current = ''
          break
        case 'tts_chunk':
          if (speakerOn) play(event.audio, event.sample_rate || 24000)
          break
        default:
          break
      }
    })
    return unsub
  }, [wsUrl, onEvent, dispatch, play, speakerOn])

  // Start call: connect WebSocket, then start mic.
  const startCall = useCallback(() => {
    // Append TTS provider as query param.
    const sep = backendUrl.includes('?') ? '&' : '?'
    setWsUrl(`${backendUrl}${sep}tts=${ttsProvider}`)
    setInCall(true)
    setTimeout(() => startMic(), 300)
  }, [backendUrl, ttsProvider, startMic])

  // End call: stop mic, close WebSocket, stop playback.
  const endCall = useCallback(() => {
    stopMic()
    stopPlayback()
    close()
    setWsUrl(null)
    setInCall(false)
    setPartial('')
    setAgentText('')
  }, [stopMic, stopPlayback, close])

  // Toggle mute.
  const toggleMute = useCallback(() => {
    setMuted((m) => !m)
  }, [])

  // Clean up on unmount.
  useEffect(() => {
    return () => {
      stopMic()
      stopPlayback()
      close()
    }
  }, [stopMic, stopPlayback, close])

  return (
    <PhoneFrame>
      <StatusBar
        phase={phase}
        wsStatus={wsStatus}
        onSettings={() => setSettingsOpen(true)}
      />

      <div className="agent-section">
        <AgentAvatar phase={phase} />
        <div className="agent-label">
          {phase === 'agent_speaking' ? 'Speaking…'
           : phase === 'agent_thinking' ? 'Thinking…'
           : phase === 'listening' ? 'Listening…'
           : inCall ? 'Connected'
           : 'Voice Agent'}
        </div>
      </div>

      <LiveTranscript partial={agentText || partial} speaker={agentText ? 'AGENT' : partialSpeaker} />

      <ConversationList messages={messages} />

      {micError && (
        <div className="error-banner">
          {micError}
        </div>
      )}

      <CallControls
        inCall={inCall}
        muted={muted}
        onMute={toggleMute}
        onEndCall={endCall}
        onStartCall={startCall}
        onStartSpeaker={() => setSpeakerOn((s) => !s)}
        speakerOn={speakerOn}
      />

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        backendUrl={backendUrl}
        onBackendUrlChange={setBackendUrl}
        ttsProvider={ttsProvider}
        onTtsProviderChange={setTtsProvider}
      />
    </PhoneFrame>
  )
}