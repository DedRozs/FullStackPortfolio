import { useEffect, useState, useRef } from 'react'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { ErrorMessage } from '../../components/catalyst-ui-kit/typescript/fieldset'
import { Subheading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import { Textarea } from '../../components/catalyst-ui-kit/typescript/textarea'

interface MessageThread {
  id: string
  subject: string
  project: string
  created_at: string
}

interface Message {
  id: string
  sender_email: string
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
        { id: msg.id, sender_email: msg.sender_email, body: msg.body, created_at: msg.created_at },
      ])
      setBody('')
    }
    setSending(false)
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-12rem)]">
      <aside className="w-64 shrink-0 flex flex-col gap-2 overflow-y-auto">
        <Subheading level={2} className="font-display uppercase tracking-widest mb-2">
          Threads
        </Subheading>
        {threads.length === 0 && <Text className="text-xs">No threads yet.</Text>}
        {threads.map((t) => (
          <Button
            key={t.id}
            onClick={() => setSelectedThread(t)}
            color={selectedThread?.id === t.id ? 'neon-cyan' : 'neon-cyan-outline'}
            className="w-full text-left justify-start"
          >
            {t.subject}
          </Button>
        ))}
      </aside>

      <div className="flex-1 flex flex-col rounded-xl border border-cyber-border bg-cyber-surface overflow-hidden">
        {!selectedThread ? (
          <div className="flex flex-1 items-center justify-center">
            <Text>Select a thread to read messages</Text>
          </div>
        ) : (
          <>
            <div className="border-b border-cyber-border px-4 py-3">
              <Subheading level={1} className="font-display text-neon-cyan">
                {selectedThread.subject}
              </Subheading>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {messages.map((m) => (
                <div key={m.id} className="flex flex-col gap-1">
                  <Text className="text-xs">
                    {m.sender_email} - {new Date(m.created_at).toLocaleString()}
                  </Text>
                  <p className="rounded-lg bg-cyber-elevated px-3 py-2 text-sm text-text-primary">
                    {m.body}
                  </p>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="border-t border-cyber-border px-4 py-3 flex gap-3 items-end">
              <Textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Type a message..."
                rows={2}
                resizable={false}
                className="flex-1"
              />
              <Button
                onClick={handleSend}
                disabled={sending || !body.trim()}
                color="neon-cyan"
              >
                Send
              </Button>
            </div>
            {error && <ErrorMessage className="px-4 pb-2">{error}</ErrorMessage>}
          </>
        )}
      </div>
    </div>
  )
}
