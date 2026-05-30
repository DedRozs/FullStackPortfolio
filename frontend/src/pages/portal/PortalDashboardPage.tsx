import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface Project {
  id: string
  name: string
  status: string
  description: string | null
  target_date: string | null
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'text-neon-cyan border-neon-cyan',
  PENDING_APPROVAL: 'text-yellow-400 border-yellow-400',
  COMPLETE: 'text-green-400 border-green-400',
  DRAFT: 'text-zinc-400 border-zinc-400',
  ARCHIVED: 'text-zinc-600 border-zinc-600',
}

export default function PortalDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    fetch('/api/portal/projects/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setProjects(data.results ?? data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-bold tracking-wider uppercase text-neon-cyan mb-2">
        Project Dashboard
      </h1>
      <p className="text-zinc-400 mb-10">Your active and recent projects.</p>

      {loading && (
        <p className="text-zinc-400 animate-pulse">Loading projects...</p>
      )}
      {error && (
        <p className="text-red-400">Failed to load projects: {error}</p>
      )}

      {!loading && !error && projects.length === 0 && (
        <p className="text-zinc-400">No projects found.</p>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => {
          const colorClass = STATUS_COLORS[project.status] ?? 'text-zinc-400 border-zinc-400'
          return (
            <Link
              key={project.id}
              to={`/portal/projects/${project.id}`}
              className="group block rounded-lg border border-zinc-700 bg-zinc-900 p-6 transition-all duration-200 hover:border-neon-cyan hover:shadow-[0_0_16px_rgba(0,255,255,0.15)]"
            >
              <div className={`mb-3 inline-block rounded border px-2 py-0.5 text-xs font-mono tracking-wider uppercase ${colorClass}`}>
                {project.status.replace('_', ' ')}
              </div>
              <h2 className="font-display text-lg font-semibold text-white group-hover:text-neon-cyan transition-colors">
                {project.name}
              </h2>
              {project.description && (
                <p className="mt-2 text-sm text-zinc-400 line-clamp-2">{project.description}</p>
              )}
              {project.target_date && (
                <p className="mt-3 text-xs text-zinc-500">
                  Target: <span className="text-zinc-300">{project.target_date}</span>
                </p>
              )}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
