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

interface FieldSchema {
  key: string
  label: string
  type: 'text' | 'number' | 'select'
  options?: string[]
  hint?: string
}

interface TriggerSchema {
  description: string
  fields: FieldSchema[]
}

const TRIGGER_SCHEMAS: Record<string, TriggerSchema> = {
  'deliverable.approved': {
    description: 'Simulate a client approving a deliverable on a project.',
    fields: [
      { key: 'status', label: 'Approval status', type: 'select', options: ['approved', 'pending', 'rejected'] },
      { key: 'deliverable_name', label: 'Deliverable name', type: 'text' },
      { key: 'project_name', label: 'Project name', type: 'text' },
      { key: 'approved_by', label: 'Approved by', type: 'text', hint: 'Name of the person who approved' },
    ],
  },
  'metric.threshold_crossed': {
    description: 'Simulate a business metric crossing a configured threshold.',
    fields: [
      { key: 'metric_type', label: 'Metric type', type: 'select', options: ['customer_growth', 'revenue', 'churn_rate'] },
      { key: 'value', label: 'Metric value', type: 'number', hint: 'Negative means decline - e.g. -8 for 8% customer loss' },
    ],
  },
  'invoice.overdue': {
    description: 'Simulate an invoice becoming overdue.',
    fields: [
      { key: 'client_name', label: 'Client name', type: 'text' },
      { key: 'invoice_id', label: 'Invoice ID', type: 'text', hint: 'e.g. INV-1001' },
      { key: 'amount', label: 'Invoice amount (USD)', type: 'number' },
      { key: 'days_overdue', label: 'Days overdue', type: 'number' },
    ],
  },
  'file.uploaded': {
    description: 'Simulate a file being uploaded to the client portal.',
    fields: [
      { key: 'file_name', label: 'File name', type: 'text', hint: 'e.g. Contract_Signed.pdf' },
      { key: 'file_type', label: 'File type', type: 'select', options: ['application/pdf', 'image/png', 'image/jpeg', 'text/csv'] },
      { key: 'uploaded_by', label: 'Uploaded by', type: 'text', hint: 'Email address of the uploader' },
    ],
  },
}

const FIELD_DEFAULTS: Record<string, Record<string, string>> = {
  'deliverable.approved': { status: 'approved', deliverable_name: 'Brand Identity V2', project_name: 'Acme Corp Rebrand', approved_by: 'Alice' },
  'metric.threshold_crossed': { metric_type: 'customer_growth', value: '-8' },
  'invoice.overdue': { client_name: 'Acme Corp', invoice_id: 'INV-1001', amount: '6200', days_overdue: '14' },
  'file.uploaded': { file_name: 'Contract_Signed.pdf', file_type: 'application/pdf', uploaded_by: 'alice@acme-corp.example.com' },
}

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

  // Dry run state
  const [dryRunRule, setDryRunRule] = useState<AutomationRule | null>(null)
  const [dryRunFormValues, setDryRunFormValues] = useState<Record<string, string>>({})
  const [dryRunRunning, setDryRunRunning] = useState(false)
  const [dryRunError, setDryRunError] = useState<string | null>(null)
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null)
  const [dryRunStep, setDryRunStep] = useState<'config' | 'result' | null>(null)

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

  function openDryRunConfig(rule: AutomationRule) {
    setDryRunRule(rule)
    setDryRunFormValues(FIELD_DEFAULTS[rule.trigger_type] ?? {})
    setDryRunError(null)
    setDryRunResult(null)
    setDryRunStep('config')
  }

  function setField(key: string, value: string) {
    setDryRunFormValues(prev => ({ ...prev, [key]: value }))
  }

  async function executeDryRun() {
    if (!dryRunRule) return
    const schema = TRIGGER_SCHEMAS[dryRunRule.trigger_type]
    const ctx: Record<string, unknown> = {}
    for (const field of schema?.fields ?? []) {
      const raw = dryRunFormValues[field.key] ?? ''
      ctx[field.key] = field.type === 'number' ? (parseFloat(raw) || 0) : raw
    }
    setDryRunRunning(true)
    setDryRunError(null)
    try {
      const res = await fetch(`${API_BASE}/rules/${dryRunRule.id}/dry_run/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ context: ctx }),
      })
      if (!res.ok) throw new Error(`Dry run failed (${res.status})`)
      const result: DryRunResult = await res.json()
      setDryRunResult(result)
      setDryRunStep('result')
    } catch (err) {
      setDryRunError(err instanceof Error ? err.message : 'Dry run failed')
    } finally {
      setDryRunRunning(false)
    }
  }

  function closeDryRun() {
    setDryRunStep(null)
    setDryRunRule(null)
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
                  <Button plain onClick={() => openDryRunConfig(rule)}>
                    Dry Run
                  </Button>
                  <Link href={`/automations/${rule.id}/runs`}>View Runs</Link>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Step 1: context configuration */}
      <Dialog open={dryRunStep === 'config'} onClose={closeDryRun}>
        <DialogTitle>
          Dry Run
          {dryRunRule && (
            <span className="ml-2 font-normal text-text-muted">- {dryRunRule.name}</span>
          )}
        </DialogTitle>
        <DialogBody>
          {dryRunRule && (() => {
            const schema = TRIGGER_SCHEMAS[dryRunRule.trigger_type]
            return (
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Text className="text-sm text-text-muted">Trigger:</Text>
                  <Badge color="sky">{dryRunRule.trigger_type}</Badge>
                </div>
                {schema ? (
                  <>
                    <p className="text-sm text-text-muted">{schema.description}</p>
                    <div className="space-y-4">
                      {schema.fields.map(field => (
                        <div key={field.key}>
                          <label className="block text-sm font-medium text-text-primary mb-1">
                            {field.label}
                          </label>
                          {field.type === 'select' ? (
                            <select
                              className="w-full bg-cyber-dark border border-cyber-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-neon-cyan"
                              value={dryRunFormValues[field.key] ?? ''}
                              onChange={e => setField(field.key, e.target.value)}
                            >
                              {field.options?.map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type={field.type}
                              className="w-full bg-cyber-dark border border-cyber-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-neon-cyan"
                              value={dryRunFormValues[field.key] ?? ''}
                              onChange={e => setField(field.key, e.target.value)}
                            />
                          )}
                          {field.hint && (
                            <p className="mt-1 text-xs text-text-muted">{field.hint}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-text-muted">No form available for this trigger type.</p>
                )}
                {dryRunError && (
                  <p className="text-red-400 text-sm">{dryRunError}</p>
                )}
              </div>
            )
          })()}
        </DialogBody>
        <DialogActions>
          <Button plain onClick={closeDryRun}>Cancel</Button>
          <Button onClick={executeDryRun} disabled={dryRunRunning}>
            {dryRunRunning ? 'Running...' : 'Run Simulation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Step 2: results */}
      <Dialog open={dryRunStep === 'result'} onClose={closeDryRun}>
        <DialogTitle>
          Dry Run Result
          {dryRunRule && (
            <span className="ml-2 font-normal text-text-muted">- {dryRunRule.name}</span>
          )}
        </DialogTitle>
        <DialogBody>
          {dryRunResult && (
            <div className="space-y-5">
              {/* Pass / fail banner */}
              <div className={`flex items-start gap-3 rounded-lg border p-3 ${
                dryRunResult.conditions_passed
                  ? 'border-neon-cyan/30 bg-neon-cyan/5'
                  : 'border-red-500/30 bg-red-500/5'
              }`}>
                {dryRunResult.conditions_passed ? (
                  <svg className="mt-0.5 size-5 shrink-0 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="mt-0.5 size-5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                <div>
                  <p className={`font-semibold text-sm ${dryRunResult.conditions_passed ? 'text-neon-cyan' : 'text-red-400'}`}>
                    {dryRunResult.conditions_passed ? 'All conditions matched' : 'Conditions not met'}
                  </p>
                  <p className="text-text-muted text-xs mt-0.5">
                    {dryRunResult.conditions_passed
                      ? 'This rule would have triggered and executed its configured actions.'
                      : 'No actions would execute with this context payload.'}
                  </p>
                </div>
              </div>

              {/* Engine log */}
              {dryRunResult.log_messages.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-widest text-text-muted mb-2">Engine output</p>
                  <div className="rounded-lg border border-cyber-border bg-cyber-dark p-3 font-mono text-sm space-y-1">
                    {dryRunResult.log_messages.map((msg, i) => (
                      <div key={i} className="flex gap-2 text-text-muted leading-relaxed">
                        <span className="text-neon-cyan/40 select-none">›</span>
                        <span>{msg}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Would-execute actions */}
              <div>
                <p className="text-xs font-medium uppercase tracking-widest text-text-muted mb-2">
                  Actions that would execute
                </p>
                {dryRunResult.would_execute_actions.length === 0 ? (
                  <p className="text-text-muted text-sm italic">No actions would execute</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {dryRunResult.would_execute_actions.map((actionType, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1.5 rounded-md border border-neon-cyan/30 bg-neon-cyan/10 px-2.5 py-1 text-xs font-medium text-neon-cyan"
                      >
                        <span className="text-neon-cyan/50">{i + 1}.</span>
                        {actionType}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setDryRunStep('config')}>Run Again</Button>
          <Button onClick={closeDryRun}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
