import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/catalyst-ui-kit/typescript/table'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'

interface AutomationRule {
  id: string
  name: string
  trigger_type: string
  is_enabled: boolean
  created_at: string
}

interface AutomationRun {
  id: string
  rule: string
  trigger_type: string
  status: string
  is_dry_run: boolean
  started_at: string | null
  completed_at: string | null
  created_at: string
}

interface RunLog {
  id: string
  run: string
  level: string
  message: string
  logged_at: string
}

const API_BASE = '/api/workflow'

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Token ${localStorage.getItem('auth_token') ?? ''}`,
  }
}

function statusColor(status: string): 'green' | 'red' | 'yellow' | 'zinc' | 'sky' {
  switch (status) {
    case 'success': return 'green'
    case 'failure': return 'red'
    case 'running': return 'yellow'
    case 'dry_run': return 'sky'
    default: return 'zinc'
  }
}

function logLevelColor(level: string): 'red' | 'yellow' | 'sky' | 'zinc' {
  switch (level.toLowerCase()) {
    case 'error': return 'red'
    case 'warning': case 'warn': return 'yellow'
    case 'info': return 'sky'
    default: return 'zinc'
  }
}

export default function AutomationRunsPage() {
  const { id } = useParams<{ id: string }>()
  const [rule, setRule] = useState<AutomationRule | null>(null)
  const [runs, setRuns] = useState<AutomationRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
  const [logs, setLogs] = useState<Record<string, RunLog[]>>({})

  useEffect(() => {
    if (!id) return
    Promise.all([
      fetch(`${API_BASE}/rules/${id}/`, { headers: authHeaders() }),
      fetch(`${API_BASE}/runs/?rule_id=${id}`, { headers: authHeaders() }),
    ])
      .then(async ([ruleRes, runsRes]) => {
        if (!ruleRes.ok) throw new Error(`Failed to load rule (${ruleRes.status})`)
        if (!runsRes.ok) throw new Error(`Failed to load runs (${runsRes.status})`)
        const [ruleData, runsData] = await Promise.all([ruleRes.json(), runsRes.json()])
        setRule(ruleData)
        setRuns(runsData)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  async function handleExpandRun(runId: string) {
    if (expandedRunId === runId) {
      setExpandedRunId(null)
      return
    }
    setExpandedRunId(runId)
    if (logs[runId]) return
    try {
      const res = await fetch(`${API_BASE}/logs/?run_id=${runId}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`Failed to load logs (${res.status})`)
      const data: RunLog[] = await res.json()
      setLogs(prev => ({ ...prev, [runId]: data }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs')
    }
  }

  if (loading) return <Text>Loading...</Text>
  if (error) return <Text className="text-red-400">{error}</Text>

  return (
    <div className="space-y-6">
      <Heading>{rule?.name ?? 'Rule'} - Runs</Heading>

      {runs.length === 0 ? (
        <Text>No runs yet.</Text>
      ) : (
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Started At</TableHeader>
              <TableHeader>Status</TableHeader>
              <TableHeader>Dry Run</TableHeader>
              <TableHeader>Logs</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {runs.map(run => (
              <>
                <TableRow
                  key={run.id}
                  onClick={() => handleExpandRun(run.id)}
                  className="cursor-pointer"
                >
                  <TableCell>
                    {run.started_at
                      ? new Date(run.started_at).toLocaleString()
                      : new Date(run.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Badge color={statusColor(run.status)}>{run.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {run.is_dry_run ? (
                      <Badge color="sky">Dry Run</Badge>
                    ) : (
                      <Badge color="zinc">Live</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Text>{expandedRunId === run.id ? 'Hide' : 'Show'}</Text>
                  </TableCell>
                </TableRow>
                {expandedRunId === run.id && (
                  <TableRow key={`${run.id}-logs`}>
                    <TableCell colSpan={4} className="bg-cyber-elevated">
                      {(logs[run.id] ?? []).length === 0 ? (
                        <Text>No log entries.</Text>
                      ) : (
                        <div className="space-y-1 py-2">
                          {(logs[run.id] ?? []).map(log => (
                            <div key={log.id} className="flex items-start gap-2">
                              <Badge color={logLevelColor(log.level)}>{log.level}</Badge>
                              <Text className="flex-1">{log.message}</Text>
                              <Text className="text-text-muted text-xs whitespace-nowrap">
                                {new Date(log.logged_at).toLocaleTimeString()}
                              </Text>
                            </div>
                          ))}
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
