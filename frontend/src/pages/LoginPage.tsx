import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

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
        headers: { 'Content-Type': 'application/json' },
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
    } catch (err) {
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
        <p className="mb-6 text-sm text-zinc-400">Sign in to access your projects.</p>

        <div className="mb-8 rounded border border-zinc-700 bg-zinc-900/60 p-4">
          <p className="mb-3 text-xs font-mono uppercase tracking-wider text-zinc-500">Demo accounts</p>
          <div className="flex flex-col gap-2">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.email}
                type="button"
                onClick={() => fillDemo(a.email)}
                className="flex items-center justify-between rounded border border-zinc-700 px-3 py-2 text-left text-xs text-zinc-300 transition hover:border-neon-cyan/60 hover:bg-neon-cyan/5 hover:text-neon-cyan"
              >
                <span className="font-mono">{a.label}</span>
                <span className="text-zinc-500">{a.email}</span>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block mb-1.5 text-xs font-mono uppercase tracking-wider text-zinc-400">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full rounded border border-zinc-600 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:border-neon-cyan focus:outline-none"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block mb-1.5 text-xs font-mono uppercase tracking-wider text-zinc-400">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded border border-zinc-600 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:border-neon-cyan focus:outline-none"
              placeholder="Password"
            />
          </div>

          {error && (
            <p className="rounded border border-red-600 bg-red-950/40 px-3 py-2 text-xs text-red-300">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded border border-neon-cyan py-2.5 text-sm font-mono uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/10 disabled:opacity-40"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
