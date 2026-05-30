import { useEffect, useState } from 'react'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { Dialog, DialogBody, DialogTitle } from '../../components/catalyst-ui-kit/typescript/dialog'
import { Field, Fieldset, FieldGroup, Label } from '../../components/catalyst-ui-kit/typescript/fieldset'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Input } from '../../components/catalyst-ui-kit/typescript/input'
import { Select } from '../../components/catalyst-ui-kit/typescript/select'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/catalyst-ui-kit/typescript/table'
import { PageSection } from '../../components/catalyst-ui-kit/typescript/page-section'

interface AlertRule {
  id: string
  name: string
  metric: string
  metric_name: string
  threshold_value: string
  operator: string
  severity: string
  status: string
  created_at: string
}

interface DashboardAlert {
  id: string
  rule: string
  rule_name: string
  metric: string
  metric_name: string
  triggered_value: string
  threshold_value: string
  operator: string
  severity: string
  status: string
  created_at: string
}

interface Metric {
  id: string
  name: string
}

const SEVERITY_COLOR: Record<string, 'cyan' | 'amber' | 'red' | 'zinc'> = {
  info: 'cyan',
  warning: 'amber',
  critical: 'red',
}

const STATUS_COLOR: Record<string, 'cyan' | 'amber' | 'green' | 'red' | 'zinc'> = {
  active: 'red',
  acknowledged: 'amber',
  resolved: 'green',
}

const RULE_STATUS_COLOR: Record<string, 'green' | 'zinc'> = {
  active: 'green',
  paused: 'zinc',
}

const OPERATOR_LABEL: Record<string, string> = {
  gt: '>',
  lt: '<',
  gte: '>=',
  lte: '<=',
  eq: '=',
}

function ruleDescription(metricName: string, operator: string, threshold: string): string {
  const op = OPERATOR_LABEL[operator] ?? operator
  const value = Number(threshold).toLocaleString('en-US', { maximumFractionDigits: 2 })
  return `${metricName} ${op} $${value}`
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Token ${token}`, 'Content-Type': 'application/json' } : {}
}

export default function DashboardAlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [alerts, setAlerts] = useState<DashboardAlert[]>([])
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    metric: '',
    threshold_value: '',
    operator: 'lt',
    severity: 'warning',
  })

  function load() {
    const headers = authHeaders()
    Promise.all([
      fetch('/api/dashboard/alert-rules/', { headers }).then((r) => r.json()),
      fetch('/api/dashboard/alerts/', { headers }).then((r) => r.json()),
      fetch('/api/dashboard/metrics/', { headers }).then((r) => r.json()),
    ])
      .then(([rulesData, alertsData, metricsData]) => {
        setRules(rulesData.results ?? rulesData)
        setAlerts(alertsData.results ?? alertsData)
        setMetrics(metricsData.results ?? metricsData)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    load()
  }, [])

  async function createRule() {
    await fetch('/api/dashboard/alert-rules/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(form),
    })
    setDialogOpen(false)
    load()
  }

  async function toggleRule(rule: AlertRule) {
    const action = rule.status === 'active' ? 'pause' : 'activate'
    await fetch(`/api/dashboard/alert-rules/${rule.id}/${action}/`, {
      method: 'POST',
      headers: authHeaders(),
    })
    load()
  }

  async function acknowledgeAlert(alert: DashboardAlert) {
    await fetch(`/api/dashboard/alerts/${alert.id}/acknowledge/`, {
      method: 'POST',
      headers: authHeaders(),
    })
    load()
  }

  async function resolveAlert(alert: DashboardAlert) {
    await fetch(`/api/dashboard/alerts/${alert.id}/resolve/`, {
      method: 'POST',
      headers: authHeaders(),
    })
    load()
  }

  return (
    <div className="flex flex-col gap-10">
      <div className="flex items-start justify-between">
        <div>
          <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-2">
            Alerts
          </Heading>
          <Text>Manage alert rules and active alerts.</Text>
        </div>
        <Button onClick={() => setDialogOpen(true)}>New Rule</Button>
      </div>

      {loading && <Text className="animate-pulse">Loading alerts...</Text>}
      {error && <Text className="text-red-400">Failed to load data: {error}</Text>}

      {!loading && !error && (
        <>
          <PageSection heading="Alert Rules">
            {rules.length === 0 ? (
              <Text>No alert rules configured.</Text>
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeader>Name</TableHeader>
                    <TableHeader>Condition</TableHeader>
                    <TableHeader>Severity</TableHeader>
                    <TableHeader>Status</TableHeader>
                    <TableHeader>Action</TableHeader>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>{rule.name}</TableCell>
                      <TableCell>
                        <span className="font-mono text-xs text-text-muted">
                          {ruleDescription(rule.metric_name, rule.operator, rule.threshold_value)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge color={SEVERITY_COLOR[rule.severity] ?? 'zinc'}>
                          {rule.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge color={RULE_STATUS_COLOR[rule.status] ?? 'zinc'}>
                          {rule.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button plain onClick={() => toggleRule(rule)}>
                          {rule.status === 'active' ? 'Pause' : 'Activate'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </PageSection>

          <PageSection heading="Active Alerts">
            {alerts.length === 0 ? (
              <Text>No active alerts.</Text>
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeader>Rule</TableHeader>
                    <TableHeader>Severity</TableHeader>
                    <TableHeader>Triggered Value</TableHeader>
                    <TableHeader>Status</TableHeader>
                    <TableHeader>Created</TableHeader>
                    <TableHeader>Actions</TableHeader>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-sm text-text-primary">{alert.rule_name}</span>
                          <span className="font-mono text-xs text-text-muted">
                            {ruleDescription(alert.metric_name, alert.operator, alert.threshold_value)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge color={SEVERITY_COLOR[alert.severity] ?? 'zinc'}>
                          {alert.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-xs text-text-muted">
                          {Number(alert.triggered_value).toLocaleString('en-US', { maximumFractionDigits: 2 })}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge color={STATUS_COLOR[alert.status] ?? 'zinc'}>
                          {alert.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(alert.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {alert.status === 'active' && (
                            <Button plain onClick={() => acknowledgeAlert(alert)}>
                              Ack
                            </Button>
                          )}
                          {alert.status !== 'resolved' && (
                            <Button plain onClick={() => resolveAlert(alert)}>
                              Resolve
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </PageSection>
        </>
      )}

      <Dialog open={dialogOpen} onClose={setDialogOpen}>
        <DialogTitle>Create Alert Rule</DialogTitle>
        <DialogBody>
          <Fieldset>
            <FieldGroup>
              <Field>
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Rule name"
                />
              </Field>
              <Field>
                <Label>Metric</Label>
                <Select
                  value={form.metric}
                  onChange={(e) => setForm({ ...form, metric: e.target.value })}
                >
                  <option value="">Select metric</option>
                  {metrics.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field>
                <Label>Threshold Value</Label>
                <Input
                  type="number"
                  value={form.threshold_value}
                  onChange={(e) => setForm({ ...form, threshold_value: e.target.value })}
                />
              </Field>
              <Field>
                <Label>Operator</Label>
                <Select
                  value={form.operator}
                  onChange={(e) => setForm({ ...form, operator: e.target.value })}
                >
                  <option value="gt">Greater than</option>
                  <option value="lt">Less than</option>
                  <option value="gte">Greater than or equal</option>
                  <option value="lte">Less than or equal</option>
                  <option value="eq">Equal</option>
                </Select>
              </Field>
              <Field>
                <Label>Severity</Label>
                <Select
                  value={form.severity}
                  onChange={(e) => setForm({ ...form, severity: e.target.value })}
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </Select>
              </Field>
            </FieldGroup>
          </Fieldset>
          <div className="mt-6 flex justify-end gap-3">
            <Button outline onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={createRule}>Create</Button>
          </div>
        </DialogBody>
      </Dialog>
    </div>
  )
}
