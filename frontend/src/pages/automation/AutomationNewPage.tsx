import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { Heading, Subheading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Input } from '../../components/catalyst-ui-kit/typescript/input'
import { Select } from '../../components/catalyst-ui-kit/typescript/select'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import { Textarea } from '../../components/catalyst-ui-kit/typescript/textarea'

const TRIGGER_TYPES = [
  { value: 'deliverable.approved', label: 'Deliverable Approved' },
  { value: 'metric.threshold_crossed', label: 'Metric Threshold Crossed' },
  { value: 'invoice.overdue', label: 'Invoice Overdue' },
  { value: 'file.uploaded', label: 'File Uploaded' },
]

const OPERATORS = [
  { value: 'gt', label: 'Greater Than' },
  { value: 'lt', label: 'Less Than' },
  { value: 'eq', label: 'Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'assigned_to', label: 'Assigned To' },
]

const ACTION_TYPES = [
  { value: 'send_email', label: 'Send Email' },
  { value: 'create_activity_event', label: 'Create Activity Event' },
  { value: 'update_status', label: 'Update Status' },
  { value: 'send_sms', label: 'Send SMS' },
]

interface ConditionRow {
  field_name: string
  operator: string
  expected_value: string
}

interface ActionRow {
  action_type: string
  parameters: string
}

const API_BASE = '/api/workflow'

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Token ${localStorage.getItem('auth_token') ?? ''}`,
  }
}

export default function AutomationNewPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Step 1
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [triggerType, setTriggerType] = useState(TRIGGER_TYPES[0].value)

  // Step 2
  const [conditions, setConditions] = useState<ConditionRow[]>([
    { field_name: '', operator: 'eq', expected_value: '' },
  ])

  // Step 3
  const [actions, setActions] = useState<ActionRow[]>([
    { action_type: 'send_email', parameters: '{}' },
  ])

  function addCondition() {
    setConditions(prev => [...prev, { field_name: '', operator: 'eq', expected_value: '' }])
  }

  function removeCondition(index: number) {
    setConditions(prev => prev.filter((_, i) => i !== index))
  }

  function updateCondition(index: number, field: keyof ConditionRow, value: string) {
    setConditions(prev => prev.map((c, i) => (i === index ? { ...c, [field]: value } : c)))
  }

  function addAction() {
    setActions(prev => [...prev, { action_type: 'send_email', parameters: '{}' }])
  }

  function removeAction(index: number) {
    setActions(prev => prev.filter((_, i) => i !== index))
  }

  function updateAction(index: number, field: keyof ActionRow, value: string) {
    setActions(prev => prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)))
  }

  async function handleSubmit() {
    setError(null)
    setSubmitting(true)
    try {
      // Create rule
      const ruleRes = await fetch(`${API_BASE}/rules/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ name, description, trigger_type: triggerType }),
      })
      if (!ruleRes.ok) throw new Error(`Failed to create rule (${ruleRes.status})`)
      const rule = await ruleRes.json()

      // Create conditions
      for (let i = 0; i < conditions.length; i++) {
        const c = conditions[i]
        if (!c.field_name.trim()) continue
        const res = await fetch(`${API_BASE}/conditions/`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({
            rule: rule.id,
            field_name: c.field_name,
            operator: c.operator,
            expected_value: c.expected_value,
            position: i,
          }),
        })
        if (!res.ok) throw new Error(`Failed to create condition (${res.status})`)
      }

      // Create actions
      for (let i = 0; i < actions.length; i++) {
        const a = actions[i]
        let params: Record<string, unknown> = {}
        try {
          params = JSON.parse(a.parameters)
        } catch {
          throw new Error(`Invalid JSON in action ${i + 1} parameters`)
        }
        const res = await fetch(`${API_BASE}/actions/`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({
            rule: rule.id,
            action_type: a.action_type,
            parameters: params,
            position: i,
          }),
        })
        if (!res.ok) throw new Error(`Failed to create action (${res.status})`)
      }

      navigate('/automations')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Heading>New Automation Rule</Heading>

      <div className="flex items-center gap-2">
        {[1, 2, 3, 4].map(s => (
          <div
            key={s}
            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
              s === step
                ? 'bg-neon-cyan text-black'
                : s < step
                ? 'bg-green-600 text-white'
                : 'bg-cyber-elevated text-text-muted'
            }`}
          >
            {s}
          </div>
        ))}
      </div>

      {error && <Text className="text-red-400">{error}</Text>}

      {/* Step 1: Trigger */}
      {step === 1 && (
        <div className="space-y-4">
          <Subheading>Trigger &amp; Rule Details</Subheading>
          <div className="space-y-1">
            <Text>Rule Name</Text>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="My automation rule" />
          </div>
          <div className="space-y-1">
            <Text>Description</Text>
            <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="Optional description" />
          </div>
          <div className="space-y-1">
            <Text>Trigger Type</Text>
            <Select value={triggerType} onChange={e => setTriggerType(e.target.value)}>
              {TRIGGER_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </Select>
          </div>
          <Button onClick={() => setStep(2)} disabled={!name.trim()}>Next</Button>
        </div>
      )}

      {/* Step 2: Conditions */}
      {step === 2 && (
        <div className="space-y-4">
          <Subheading>Conditions</Subheading>
          {conditions.map((c, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 items-end">
              <div className="space-y-1">
                <Text>Field</Text>
                <Input
                  value={c.field_name}
                  onChange={e => updateCondition(i, 'field_name', e.target.value)}
                  placeholder="field_name"
                />
              </div>
              <div className="space-y-1">
                <Text>Operator</Text>
                <Select value={c.operator} onChange={e => updateCondition(i, 'operator', e.target.value)}>
                  {OPERATORS.map(op => (
                    <option key={op.value} value={op.value}>{op.label}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <Text>Expected Value</Text>
                <Input
                  value={c.expected_value}
                  onChange={e => updateCondition(i, 'expected_value', e.target.value)}
                  placeholder="value"
                />
              </div>
              <Button plain onClick={() => removeCondition(i)} disabled={conditions.length === 1}>
                Remove
              </Button>
            </div>
          ))}
          <Button plain onClick={addCondition}>+ Add Condition</Button>
          <div className="flex gap-2">
            <Button plain onClick={() => setStep(1)}>Back</Button>
            <Button onClick={() => setStep(3)}>Next</Button>
          </div>
        </div>
      )}

      {/* Step 3: Actions */}
      {step === 3 && (
        <div className="space-y-4">
          <Subheading>Actions</Subheading>
          {actions.map((a, i) => (
            <div key={i} className="space-y-2 rounded-lg border border-cyber-border p-4">
              <div className="grid grid-cols-[1fr_auto] gap-2 items-end">
                <div className="space-y-1">
                  <Text>Action Type</Text>
                  <Select value={a.action_type} onChange={e => updateAction(i, 'action_type', e.target.value)}>
                    {ACTION_TYPES.map(at => (
                      <option key={at.value} value={at.value}>{at.label}</option>
                    ))}
                  </Select>
                </div>
                <Button plain onClick={() => removeAction(i)} disabled={actions.length === 1}>
                  Remove
                </Button>
              </div>
              <div className="space-y-1">
                <Text>Parameters (JSON)</Text>
                <Textarea
                  value={a.parameters}
                  onChange={e => updateAction(i, 'parameters', e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          ))}
          <Button plain onClick={addAction}>+ Add Action</Button>
          <div className="flex gap-2">
            <Button plain onClick={() => setStep(2)}>Back</Button>
            <Button onClick={() => setStep(4)}>Next</Button>
          </div>
        </div>
      )}

      {/* Step 4: Review */}
      {step === 4 && (
        <div className="space-y-4">
          <Subheading>Review</Subheading>
          <div className="rounded-lg border border-cyber-border p-4 space-y-3">
            <div>
              <Text className="text-text-muted text-xs uppercase tracking-wide">Rule Name</Text>
              <Text>{name}</Text>
            </div>
            {description && (
              <div>
                <Text className="text-text-muted text-xs uppercase tracking-wide">Description</Text>
                <Text>{description}</Text>
              </div>
            )}
            <div>
              <Text className="text-text-muted text-xs uppercase tracking-wide">Trigger Type</Text>
              <Text>{triggerType}</Text>
            </div>
            <div>
              <Text className="text-text-muted text-xs uppercase tracking-wide">Conditions ({conditions.filter(c => c.field_name.trim()).length})</Text>
              {conditions.filter(c => c.field_name.trim()).map((c, i) => (
                <Text key={i}>{c.field_name} {c.operator} {c.expected_value}</Text>
              ))}
            </div>
            <div>
              <Text className="text-text-muted text-xs uppercase tracking-wide">Actions ({actions.length})</Text>
              {actions.map((a, i) => (
                <Text key={i}>{a.action_type}</Text>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <Button plain onClick={() => setStep(3)}>Back</Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Rule'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
