import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { Dialog, DialogActions, DialogBody, DialogTitle } from '../../components/catalyst-ui-kit/typescript/dialog'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Link } from '../../components/catalyst-ui-kit/typescript/link'
import { Switch } from '../../components/catalyst-ui-kit/typescript/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/catalyst-ui-kit/typescript/table'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'

interface AutomationRule {
  id: string
  name: string
  description: string | null
  trigger_type: string
  is_enabled: boolean
  created_at: string
}

interface DryRunResult {
  rule_id: string
  conditions_passed: boolean
  log_messages: string[]
  would_execute_actions: string[]
}

const API_BASE = '/api/workflow'

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Token ${localStorage.getItem('auth_token') ?? ''}`,
  }
}

export default function AutomationListPage() {
  const navigate = useNavigate()
  const [rules, setRules] = useState<AutomationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null)
  const [dryRunDialogOpen, setDryRunDialogOpen] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/rules/`, { headers: authHeaders() })
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load rules (${res.status})`)
        return res.json()
      })
      .then(data => setRules(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleToggleEnabled(rule: AutomationRule) {
    try {
      const res = await fetch(`${API_BASE}/rules/${rule.id}/`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ is_enabled: !rule.is_enabled }),
      })
      if (!res.ok) throw new Error(`Toggle failed (${res.status})`)
      const updated: AutomationRule = await res.json()
      setRules(prev => prev.map(r => (r.id === updated.id ? updated : r)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Toggle failed')
    }
  }

  async function handleDryRun(rule: AutomationRule) {
    try {
      const res = await fetch(`${API_BASE}/rules/${rule.id}/dry_run/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ context: {} }),
      })
      if (!res.ok) throw new Error(`Dry run failed (${res.status})`)
      const result: DryRunResult = await res.json()
      setDryRunResult(result)
      setDryRunDialogOpen(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dry run failed')
    }
  }

  if (loading) return <Text>Loading...</Text>
  if (error) return <Text className="text-red-400">{error}</Text>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Heading>Automation Rules</Heading>
        <Button onClick={() => navigate('/automations/new')}>New Rule</Button>
      </div>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeader>Name</TableHeader>
            <TableHeader>Trigger</TableHeader>
            <TableHeader>Enabled</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableRow>
        </TableHead>
        <TableBody>
          {rules.map(rule => (
            <TableRow key={rule.id}>
              <TableCell className="font-medium">{rule.name}</TableCell>
              <TableCell>
                <Badge color="sky">{rule.trigger_type}</Badge>
              </TableCell>
              <TableCell>
                <Switch
                  checked={rule.is_enabled}
                  onChange={() => handleToggleEnabled(rule)}
                  color="green"
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Button plain onClick={() => handleDryRun(rule)}>
                    Dry Run
                  </Button>
                  <Link href={`/automations/${rule.id}/runs`}>View Runs</Link>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={dryRunDialogOpen} onClose={() => setDryRunDialogOpen(false)}>
        <DialogTitle>Dry Run Result</DialogTitle>
        <DialogBody>
          {dryRunResult && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Text>Conditions passed:</Text>
                <Badge color={dryRunResult.conditions_passed ? 'green' : 'red'}>
                  {dryRunResult.conditions_passed ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div>
                <Text className="font-medium mb-1">Log messages:</Text>
                {dryRunResult.log_messages.length === 0 ? (
                  <Text>None</Text>
                ) : (
                  <ul className="list-disc list-inside space-y-1">
                    {dryRunResult.log_messages.map((msg, i) => (
                      <li key={i}><Text>{msg}</Text></li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <Text className="font-medium mb-1">Would execute actions:</Text>
                {dryRunResult.would_execute_actions.length === 0 ? (
                  <Text>None</Text>
                ) : (
                  <ul className="list-disc list-inside space-y-1">
                    {dryRunResult.would_execute_actions.map((action, i) => (
                      <li key={i}><Text>{JSON.stringify(action)}</Text></li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </DialogBody>
        <DialogActions>
          <Button onClick={() => setDryRunDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
