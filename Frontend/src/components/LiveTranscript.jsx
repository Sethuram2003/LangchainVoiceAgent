import './LiveTranscript.css'
import { speakerColor } from '../utils/format'

/** LiveTranscript — caption-style strip showing the current partial transcript. */
export function LiveTranscript({ partial, speaker }) {
  if (!partial) return null
  const sp = speaker || 'UNKNOWN'
  return (
    <div className="live-tx">
      <span className="live-tx-speaker" style={{ color: speakerColor(sp) }}>
        ● Speaker {sp}
      </span>
      <span className="live-tx-text">{partial}</span>
    </div>
  )
}