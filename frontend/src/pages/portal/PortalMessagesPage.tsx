import { useEffect, useState, useRef } from 'react'

interface MessageThread {
  id: string
  subject: string
  project: string
  created_at: string
}

interface Message {
  id: string
  sender: string
  body: string
  created_at: string
}

export default function PortalMessagesPage() {
  const token = localStorage.getItem('auth_token')
  const headers = { Authorization: `Token ${token}` }

  const [threads, setThreads] = useState<MessageThread[]>([])
  const [selectedThread, setSelectedThread] = useState<MessageThread | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/portal/threads/', { headers })
      .then((r) => r.json())
      .then((d) => setThreads(d.results ?? d))
  }, [])

  useEffect(() => {
    if (!selectedThread) return
    fetch(`/api/portal/messages/?thread=${selectedThread.id}`, { headers })
      .then((r) => r.json())
      .then((d) => {
        setMessages(d.results ?? d)
      })
  }, [selectedThread])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    if (!body.trim() || !selectedThread) return
    setSending(true)
    setError(null)
    const res = await fetch('/api/portal/messages/send/', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: selectedThread.id, body }),
    })
    if (!res.ok) {
      const data = await res.json()
      setError(data.detail ?? 'Send failed')
    } else {
      const msg = await res.json()
      setMessages((prev) => [
        ...prev,
        { id: msg.id, sender: 'You', body: msg.body, created_at: msg.created_at },
      ])
      setBody('')
    }
    setSending(false)
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 flex gap-6 h-[calc(100vh-8rem)]">
      <aside className="w-64 shrink-0 flex flex-col gap-2 overflow-y-auto">
        <h2 className="font-display text-sm uppercase tracking-widest text-zinc-400 mb-2">
          Threads
        </h2>
        {threads.length === 0 && (
          <p className="text-xs text-zinc-500">No threads yet.</p>
        )}
        {threads.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedThread(t)}
            className={`rounded border px-3 py-2 text-left text-sm transition ${
              selectedThread?.id === t.id
                ? 'border-neon-cyan bg-neon-cyan/10 text-neon-cyan'
                : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500'
            }`}
          >
            {t.subject}
          </button>
        ))}
      </aside>

      <div className="flex-1 flex flex-col rounded border border-zinc-700 bg-zinc-900 overflow-hidden">
        {!selectedThread ? (
          <div className="flex flex-1 items-center justify-center text-zinc-500 text-sm">
            Select a thread to read messages
          </div>
        ) : (
          <>
            <div className="border-b border-zinc-700 px-4 py-3">
              <h1 className="font-display text-base font-semibold text-neon-cyan">
                {selectedThread.subject}
              </h1>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {messages.map((m) => (
                <div key={m.id} className="flex flex-col gap-1">
                  <span className="text-xs text-zinc-500">
                    {m.sender} - {new Date(m.created_at).toLocaleString()}
                  </span>
                  <p className="rounded bg-zinc-800 px-3 py-2 text-sm text-zinc-200">{m.body}</p>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="border-t border-zinc-700 px-4 py-3 flex gap-3">
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Type a message..."
                rows={2}
                className="flex-1 resize-none rounded border border-zinc-600 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:border-neon-cyan focus:outline-none"
              />
              <button
                onClick={handleSend}
                disabled={sending || !body.trim()}
                className="self-end rounded border border-neon-cyan px-4 py-2 text-xs font-mono uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/10 disabled:opacity-40"
              >
                Send
              </button>
            </div>
            {error && <p className="px-4 pb-2 text-xs text-red-400">{error}</p>}
          </>
        )}
      </div>
    </div>
  )
}
