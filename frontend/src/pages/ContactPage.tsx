import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Field, ErrorMessage, Label } from '../components/catalyst-ui-kit/typescript/fieldset'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Input } from '../components/catalyst-ui-kit/typescript/input'
import { Link } from '../components/catalyst-ui-kit/typescript/link'
import { Text } from '../components/catalyst-ui-kit/typescript/text'
import { Textarea } from '../components/catalyst-ui-kit/typescript/textarea'

interface FormState {
  name: string
  email: string
  subject: string
  message: string
}

type SubmitStatus = 'idle' | 'loading' | 'success' | 'error'

const EMPTY_FORM: FormState = { name: '', email: '', subject: '', message: '' }

const LABEL_CLASS = 'text-xs font-display tracking-widest uppercase text-text-muted'

const CONTACT_LINKS = [
  {
    label: 'LinkedIn',
    href: 'https://linkedin.com/in/thejprince',
    description: 'linkedin.com/in/thejprince',
  },
  {
    label: 'GitHub',
    href: 'https://github.com/dedrozs',
    description: 'github.com/dedrozs',
  },
]

export default function ContactPage() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [status, setStatus] = useState<SubmitStatus>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleTextareaChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    try {
      const response = await fetch('/api/contact/submit/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error ?? 'Something went wrong.')
      }

      setStatus('success')
      setForm(EMPTY_FORM)
    } catch (err) {
      setStatus('error')
      setErrorMessage(err instanceof Error ? err.message : 'Unexpected error.')
    }
  }

  return (
    <>
      {/* Hero */}
      <section className="scanlines relative pt-20 pb-10 flex flex-col items-center text-center px-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,27,114,0.4) 0%, transparent 70%)',
          }}
        />
        <Text
          className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3 animate-fade-in-up"
          style={{ animationDelay: '0s' }}
        >
          Available for Engagements
        </Text>
        <Heading
          level={1}
          className="font-display text-4xl sm:text-5xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          Contact
        </Heading>
        <Text
          className="text-lg max-w-2xl leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Open to consulting engagements and senior engineering roles. Fill out the form
          or reach out directly on LinkedIn.
        </Text>
      </section>

      {/* Content */}
      <section className="relative overflow-hidden py-20">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,255,255,0.04) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6 grid sm:grid-cols-[1fr_2fr] gap-12 items-start">

          {/* Left - contact info */}
          <div className="flex flex-col gap-6">
            <div>
              <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
                Reach Out
              </Text>
              <Heading level={2} className="font-display text-xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-4">
                Let&apos;s Talk
              </Heading>
              <Text className="text-sm leading-relaxed">
                Whether you have a project in mind, need a senior engineer on your team,
                or just want to connect - send a message and I&apos;ll respond within
                one business day.
              </Text>
            </div>

            <div className="flex flex-col gap-3">
              {CONTACT_LINKS.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-4 hover:border-neon-cyan/50 transition-colors"
                >
                  <span className="font-display text-xs font-bold text-neon-cyan tracking-widest uppercase w-16 shrink-0">
                    {link.label}
                  </span>
                  <span className="text-text-muted text-xs font-mono truncate">
                    {link.description}
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* Right - form */}
          <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-8 py-8">
            {status === 'success' ? (
              <div className="flex flex-col items-center justify-center text-center py-16 gap-4">
                <div className="w-12 h-12 rounded-full border-2 border-neon-green flex items-center justify-center">
                  <span className="text-neon-green text-xl select-none">&#10003;</span>
                </div>
                <p className="text-neon-green font-display tracking-wider uppercase text-sm">
                  Message received.
                </p>
                <Text className="text-sm">
                  I&apos;ll be in touch within one business day.
                </Text>
                <Button
                  color="neon-cyan-outline"
                  onClick={() => setStatus('idle')}
                  className="mt-4 font-display tracking-widest uppercase text-xs"
                >
                  Send Another
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                <Field>
                  <Label className={LABEL_CLASS}>
                    Name<span className="text-neon-magenta ml-1">*</span>
                  </Label>
                  <Input name="name" value={form.name} onChange={handleInputChange} required />
                </Field>

                <Field>
                  <Label className={LABEL_CLASS}>
                    Email<span className="text-neon-magenta ml-1">*</span>
                  </Label>
                  <Input type="email" name="email" value={form.email} onChange={handleInputChange} required />
                </Field>

                <Field>
                  <Label className={LABEL_CLASS}>Subject</Label>
                  <Input name="subject" value={form.subject} onChange={handleInputChange} />
                </Field>

                <Field>
                  <Label className={LABEL_CLASS}>
                    Message<span className="text-neon-magenta ml-1">*</span>
                  </Label>
                  <Textarea
                    name="message"
                    value={form.message}
                    onChange={handleTextareaChange}
                    required
                    rows={6}
                    resizable={false}
                  />
                </Field>

                {status === 'error' && (
                  <ErrorMessage>{errorMessage}</ErrorMessage>
                )}

                <Button
                  type="submit"
                  color="neon-cyan"
                  disabled={status === 'loading'}
                  className="w-full font-display tracking-widest uppercase"
                >
                  {status === 'loading' ? 'Sending...' : 'Send Message'}
                </Button>
              </form>
            )}
          </div>
        </div>
      </section>
    </>
  )
}
