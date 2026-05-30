import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Field, FieldGroup, Label, ErrorMessage } from '../components/catalyst-ui-kit/typescript/fieldset'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Input } from '../components/catalyst-ui-kit/typescript/input'
import { Text } from '../components/catalyst-ui-kit/typescript/text'
import { getCsrfToken } from '../lib/csrf'
import { setStaff } from '../lib/auth'

const DEMO_ACCOUNTS = [
  { label: 'Acme Corp (client)', email: 'alice@acme-corp.example.com' },
  { label: 'Nova Ventures (client)', email: 'bob@nova-ventures.example.com' },
  { label: 'Staff admin - Dashboard + Automations', email: 'staff@example.com' },
] as const

const DEMO_PASSWORD = 'PortalDemo2025!'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from ?? '/portal'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function fillDemo(demoEmail: string) {
    setEmail(demoEmail)
    setPassword(DEMO_PASSWORD)
    setError(null)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.non_field_errors?.[0] ?? data.detail ?? 'Login failed')
        return
      }
      const token = data.key ?? data.access
      if (!token) {
        setError('No token received from server')
        return
      }
      localStorage.setItem('auth_token', token)
      const profileRes = await fetch('/api/auth/user/', {
        headers: { Authorization: `Token ${token}` },
      })
      if (profileRes.ok) {
        const profile = await profileRes.json()
        setStaff(profile.is_staff === true)
      }
      navigate(from)
    } catch {
      setError('Network error - please try again')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Hero */}
      <section className="scanlines relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(255,0,255,0.06) 0%, rgba(0,255,255,0.04) 40%, transparent 70%)',
          }}
        />

        <div className="w-full max-w-sm">
          {/* Header */}
          <div className="mb-8 text-center">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Welcome Back
            </Text>
            <Heading
              level={1}
              className="font-display text-3xl font-bold tracking-wider uppercase text-neon-cyan glow-cyan mb-3"
            >
              Sign In
            </Heading>
            <Text className="text-sm leading-relaxed">
              Access the client portal, ops dashboard, or automations engine.
            </Text>
          </div>

          {/* Demo accounts */}
          <div className="mb-8 rounded-xl border border-cyber-border bg-cyber-surface p-4">
            <p className="mb-3 text-xs font-display tracking-[0.3em] uppercase text-text-muted">
              Demo accounts
            </p>
            <div className="flex flex-col gap-2">
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.email}
                  type="button"
                  onClick={() => fillDemo(a.email)}
                  className="flex items-center justify-between rounded-lg border border-cyber-border bg-cyber-elevated px-3 py-2 text-left text-xs transition hover:border-neon-cyan hover:text-neon-cyan focus:outline-2 focus:outline-offset-2 focus:outline-neon-cyan"
                >
                  <span className="font-mono text-text-primary">{a.label}</span>
                  <span className="font-mono text-text-muted">{a.email}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <Label className="text-xs font-display tracking-widest uppercase">Email</Label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </Field>

              <Field>
                <Label className="text-xs font-display tracking-widest uppercase">Password</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="Password"
                />
              </Field>
            </FieldGroup>

            {error && (
              <ErrorMessage className="mt-4">{error}</ErrorMessage>
            )}

            <Button
              type="submit"
              disabled={loading}
              color="neon-cyan"
              className="mt-6 w-full font-display tracking-widest uppercase"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </div>
      </section>
    </>
  )
}
