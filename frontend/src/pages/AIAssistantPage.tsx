import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Input } from '../components/catalyst-ui-kit/typescript/input'

interface Message {
  role: 'assistant' | 'user'
  content: string
}

type ModelKey = 'gpt-4o' | 'claude-sonnet-4-6'

interface ModelOption {
  key: ModelKey
  label: string
  provider: 'openai' | 'anthropic'
}

const MODELS: ModelOption[] = [
  { key: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  { key: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6', provider: 'anthropic' },
]

const DEFAULT_MODEL: ModelKey = 'claude-sonnet-4-6'

const INTRO: Message = {
  role: 'assistant',
  content:
    "Hi! I'm an AI assistant representing Joseph Prince. Joseph is a Full Stack Developer " +
    "specializing in Django, React, and cloud architecture. He's open to senior developer " +
    "roles and consulting engagements. What would you like to know about his background or work?",
}

const SUGGESTED_PROMPTS = [
  "What's Joseph's tech stack?",
  'Tell me about his experience as CTO.',
  'What projects is he currently building?',
  'Is he available for consulting?',
]

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([INTRO])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<ModelKey>(DEFAULT_MODEL)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return

    const userMessage: Message = { role: 'user', content: text.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/ai/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage], model: selectedModel }),
      })

      if (!response.ok) throw new Error('Request failed.')

      const data = await response.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    sendMessage(input)
  }

  function handleSuggestedPrompt(prompt: string) {
    sendMessage(prompt)
  }

  const showSuggestions = !loading

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Compact hero */}
      <section className="scanlines relative pt-14 pb-8 flex flex-col items-center text-center px-6 overflow-hidden shrink-0">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 120% at 50% 0%, rgba(59,27,114,0.5) 0%, transparent 70%)',
          }}
        />
        <p
          className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-2 animate-fade-in-up"
          style={{ animationDelay: '0s' }}
        >
          Powered by OpenAI &amp; Anthropic
        </p>
        <h1
          className="font-display text-3xl sm:text-4xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-3 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          AI Assistant
        </h1>
        <p
          className="text-text-muted text-sm max-w-lg leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Ask me anything about Joseph's experience, tech stack, projects, or availability.
          I have full context on his background and work.
        </p>
      </section>

      {/* Chat panel - flex-1 fills remaining viewport */}
      <section className="flex-1 flex flex-col min-h-0 px-6 pb-4">
        <div
          className="pointer-events-none absolute inset-x-0 h-64 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,255,255,0.03) 0%, transparent 70%)',
          }}
        />
        <div className="flex-1 flex flex-col min-h-0 max-w-5xl w-full mx-auto">

          {/* Chat window */}
          <div className="flex-1 flex flex-col min-h-0 bg-cyber-surface border border-cyber-border rounded-xl overflow-hidden">

            {/* Chat header strip */}
            <div className="shrink-0 flex items-center gap-3 px-5 py-3 border-b border-cyber-border bg-cyber-elevated flex-wrap">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-neon-green animate-pulse" />
              </div>
              <span className="text-[10px] font-display tracking-widest uppercase text-neon-green">
                Online
              </span>
              <span className="text-cyber-border mx-1">|</span>
              <span className="text-[10px] font-display tracking-widest uppercase text-text-muted">
                Joseph Prince AI
              </span>
              <div className="ml-auto flex items-center gap-2">
                {MODELS.map((m) => (
                  <button
                    key={m.key}
                    type="button"
                    onClick={() => setSelectedModel(m.key)}
                    disabled={loading}
                    className={[
                      'px-2.5 py-1 text-[9px] font-display tracking-widest uppercase rounded-md border transition-colors',
                      selectedModel === m.key
                        ? m.provider === 'anthropic'
                          ? 'bg-neon-magenta/15 border-neon-magenta/60 text-neon-magenta'
                          : 'bg-neon-cyan/15 border-neon-cyan/60 text-neon-cyan'
                        : 'border-cyber-border text-text-muted hover:border-neon-cyan/40 hover:text-text-primary',
                      loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
                    ].join(' ')}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-5">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="shrink-0 w-7 h-7 rounded-full border border-neon-cyan/50 bg-neon-cyan/10 flex items-center justify-center mt-0.5">
                      <span className="text-neon-cyan text-[10px] font-display font-bold leading-none">AI</span>
                    </div>
                  )}
                  <div
                    className={[
                      'max-w-[78%] px-4 py-3 text-sm leading-relaxed rounded-xl',
                      msg.role === 'assistant'
                        ? 'bg-cyber-elevated border border-neon-cyan/20 text-text-primary'
                        : 'bg-neon-magenta/10 border border-neon-magenta/30 text-text-primary',
                    ].join(' ')}
                  >
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
                          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold text-neon-cyan">{children}</strong>,
                          em: ({ children }) => <em className="italic text-text-muted">{children}</em>,
                          code: ({ children }) => <code className="px-1 py-0.5 rounded bg-cyber-surface font-mono text-xs text-neon-magenta">{children}</code>,
                          h1: ({ children }) => <h1 className="font-display font-bold text-base mb-1 text-neon-cyan">{children}</h1>,
                          h2: ({ children }) => <h2 className="font-display font-bold text-sm mb-1 text-neon-cyan">{children}</h2>,
                          h3: ({ children }) => <h3 className="font-semibold text-sm mb-1 text-text-primary">{children}</h3>,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="shrink-0 w-7 h-7 rounded-full bg-neon-magenta/20 border border-neon-magenta/50 flex items-center justify-center mt-0.5">
                      <span className="text-neon-magenta text-[11px] leading-none select-none">&#9654;</span>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3 justify-start">
                  <div className="shrink-0 w-7 h-7 rounded-full border border-neon-cyan/50 bg-neon-cyan/10 flex items-center justify-center mt-0.5">
                    <span className="text-neon-cyan text-[10px] font-display font-bold leading-none">AI</span>
                  </div>
                  <div className="bg-cyber-elevated border border-neon-cyan/20 rounded-xl px-4 py-3">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan/60 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Bottom bar: suggestions + input */}
            <div className="shrink-0 border-t border-cyber-border bg-cyber-elevated px-5 py-4 flex flex-col gap-3">
              {/* Suggested prompts */}
              {showSuggestions && (
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleSuggestedPrompt(prompt)}
                      className="px-3 py-1.5 text-xs font-display tracking-wide text-neon-cyan/80 border border-neon-cyan/30 rounded-lg hover:border-neon-cyan/70 hover:text-neon-cyan hover:bg-neon-cyan/5 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              )}

              {/* Input row */}
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask anything about Joseph's work..."
                  className="flex-1"
                />
                <Button
                  type="submit"
                  color="neon-cyan"
                  disabled={!input.trim() || loading}
                  className="font-display tracking-widest uppercase shrink-0"
                >
                  Send
                </Button>
              </form>
            </div>
          </div>

        </div>
      </section>
    </div>
  )
}
