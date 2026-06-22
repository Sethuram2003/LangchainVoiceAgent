import { useEffect, useRef } from 'react'
import './ConversationList.css'
import { speakerColor, speakerBg, fmtTime } from '../utils/format'

/**
 * ConversationList — scrollable chat with color-coded speaker bubbles.
 * Speaker messages are left-aligned, agent messages right-aligned.
 */
export function ConversationList({ messages }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="convo-empty">
        <div className="convo-empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2"
            strokeLinecap="round" strokeLinejoin="round" width="36" height="36">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </div>
        <p>Start a call to begin</p>
        <span>Press the green button below</span>
      </div>
    )
  }

  return (
    <div className="convo" ref={scrollRef}>
      {messages.map((msg) => {
        if (msg.role === 'agent') {
          return (
            <div key={msg.id} className="msg msg--agent">
              <div className="msg-bubble msg-bubble--agent">
                <div className="msg-speaker msg-speaker--agent">Agent</div>
                <div className="msg-text">{msg.text}</div>
                <div className="msg-time">{fmtTime(msg.ts)}</div>
              </div>
            </div>
          )
        }
        const sp = msg.speaker || 'UNKNOWN'
        return (
          <div key={msg.id} className="msg msg--user">
            <div
              className="msg-bubble msg-bubble--user"
              style={{
                borderColor: speakerColor(sp),
                background: speakerBg(sp),
              }}
            >
              <div className="msg-speaker" style={{ color: speakerColor(sp) }}>
                Speaker {sp}
              </div>
              <div className="msg-text">{msg.text}</div>
              <div className="msg-time">{fmtTime(msg.ts)}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}