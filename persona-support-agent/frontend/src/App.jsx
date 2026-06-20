import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const PERSONA_STYLES = {
  'Technical Expert': { color: '#2563eb', bg: '#eff6ff', label: '🛠️ Technical Expert' },
  'Frustrated User': { color: '#dc2626', bg: '#fef2f2', label: '😤 Frustrated User' },
  'Business Executive': { color: '#7c3aed', bg: '#f5f3ff', label: '📊 Business Executive' },
}

function PersonaBadge({ persona }) {
  const style = PERSONA_STYLES[persona] || { color: '#444', bg: '#eee', label: persona }
  return (
    <span className="badge" style={{ color: style.color, background: style.bg }}>
      {style.label}
    </span>
  )
}

function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null
  return (
    <div className="sources">
      <div className="sources-title">Retrieved sources</div>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <span className="source-name">{s.source}</span>
            {s.page ? <span className="source-meta"> · page {s.page}</span> : null}
            {s.section ? <span className="source-meta"> · {s.section}</span> : null}
            <span className="source-score"> · score {s.score}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function HandoffSummary({ summary }) {
  if (!summary) return null
  return (
    <div className="handoff">
      <div className="handoff-title">🚨 Human Handoff Summary</div>
      <pre>{JSON.stringify(summary, null, 2)}</pre>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const { data } = await axios.post(`${API_BASE}/chat`, {
        message: text,
        session_id: sessionId,
      })
      setSessionId(data.session_id)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.response,
          persona: data.persona,
          sources: data.retrieved_sources,
          escalated: data.escalated,
          escalationReasons: data.escalation_reasons,
          handoffSummary: data.handoff_summary,
        },
      ])
    } catch (e) {
      setError('Could not reach the support agent backend. Is the API running on ' + API_BASE + '?')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Persona-Adaptive Support Agent</h1>
        <p className="subtitle">Detects your persona, retrieves grounded answers, escalates when needed.</p>
      </header>

      <main className="chat-window">
        {messages.length === 0 && (
          <div className="empty-state">
            Try: "Our production API key stopped working with a 401, check the logs!" or
            "I've tried everything and nothing works, this is so frustrating!" or
            "What's the business impact and resolution timeline for this outage?"
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`message-row ${m.role}`}>
            <div className={`bubble ${m.role}`}>
              {m.role === 'assistant' && m.persona && (
                <div className="meta-row">
                  <PersonaBadge persona={m.persona} />
                  {m.escalated && <span className="escalated-badge">Escalated</span>}
                </div>
              )}
              <div className="bubble-text">{m.text}</div>
              {m.role === 'assistant' && <SourcesList sources={m.sources} />}
              {m.role === 'assistant' && m.escalated && (
                <div className="escalation-reasons">
                  Reasons: {m.escalationReasons?.join('; ')}
                </div>
              )}
              {m.role === 'assistant' && m.handoffSummary && (
                <HandoffSummary summary={m.handoffSummary} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="bubble assistant typing">Thinking…</div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}
        <div ref={bottomRef} />
      </main>

      <footer className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your support message…"
          rows={2}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  )
}
