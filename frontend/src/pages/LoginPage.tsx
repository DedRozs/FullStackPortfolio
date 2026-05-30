import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Field, FieldGroup, Label, ErrorMessage } from '../components/catalyst-ui-kit/typescript/fieldset'
import { Input } from '../components/catalyst-ui-kit/typescript/input'
import { getCsrfToken } from '../lib/csrf'

const DEMO_ACCOUNTS = [
  { label: 'Acme Corp (client)', email: 'alice@acme-corp.example.com' },
  { label: 'Nova Ventures (client)', email: 'bob@nova-ventures.example.com' },
  { label: 'Staff admin', email: 'staff@example.com' },
] as const

const DEMO_PASSWORD = 'PortalDemo2025!'

export default function LoginPage() {
  const navigate = useNavigate()
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
      navigate('/portal')
    } catch {
      setError('Network error - please try again')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-6">
      <div className="w-full max-w-sm">
        <h1 className="mb-2 font-display text-3xl font-bold tracking-wider uppercase text-neon-cyan">
          Client Portal
        </h1>
        <p className="mb-6 text-sm text-text-muted">Sign in to access your projects.</p>

        <div className="mb-8 rounded-xl border border-cyber-border bg-cyber-surface p-4">
          <p className="mb-3 text-xs font-mono uppercase tracking-wider text-text-muted">Demo accounts</p>
          <div className="flex flex-col gap-2">
            {DEMO_ACCOUNTS.map((a) => (
              <Button
                key={a.email}
                type="button"
                color="neon-cyan-outline"
                onClick={() => fillDemo(a.email)}
                className="flex items-center justify-between text-left text-xs"
              >
                <span className="font-mono">{a.label}</span>
                <span className="opacity-60">{a.email}</span>
              </Button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <FieldGroup>
            <Field>
              <Label className="text-xs font-mono uppercase tracking-wider">Email</Label>
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
              <Label className="text-xs font-mono uppercase tracking-wider">Password</Label>
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
            className="mt-6 w-full"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </div>
    </div>
  )
}
