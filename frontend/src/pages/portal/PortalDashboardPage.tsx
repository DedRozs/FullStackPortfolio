import { useEffect, useState } from 'react'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from '../../components/catalyst-ui-kit/typescript/card'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'

interface Project {
  id: string
  name: string
  status: string
  description: string | null
  target_date: string | null
}

const STATUS_COLOR: Record<string, 'cyan' | 'yellow' | 'green' | 'zinc'> = {
  ACTIVE: 'cyan',
  PENDING_APPROVAL: 'yellow',
  COMPLETE: 'green',
  DRAFT: 'zinc',
  ARCHIVED: 'zinc',
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
    <div>
      <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-2">
        Project Dashboard
      </Heading>
      <Text className="mb-10">Your active and recent projects.</Text>

      {loading && <Text className="animate-pulse">Loading projects...</Text>}
      {error && <Text className="text-red-400">Failed to load projects: {error}</Text>}
      {!loading && !error && projects.length === 0 && <Text>No projects found.</Text>}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Card
            key={project.id}
            href={`/portal/projects/${project.id}`}
            flush
            accent="cyan"
          >
            <CardHeader>
              <Badge color={STATUS_COLOR[project.status] ?? 'zinc'}>
                {project.status.replace('_', ' ')}
              </Badge>
              <CardTitle>{project.name}</CardTitle>
            </CardHeader>
            <CardBody>
              {project.description && (
                <CardDescription className="line-clamp-2">{project.description}</CardDescription>
              )}
              {project.target_date && (
                <Text className="text-xs">
                  Target: <span className="text-text-primary">{project.target_date}</span>
                </Text>
              )}
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  )
}
