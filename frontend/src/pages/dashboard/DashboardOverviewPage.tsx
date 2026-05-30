import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/catalyst-ui-kit/typescript/table'
import { KpiCard } from '../../components/catalyst-ui-kit/typescript/kpi-card'
import { KpiGrid } from '../../components/catalyst-ui-kit/typescript/kpi-grid'
import { ChartContainer } from '../../components/catalyst-ui-kit/typescript/chart-container'
import { PageSection } from '../../components/catalyst-ui-kit/typescript/page-section'

interface RevenueSnapshot {
  id: string
  amount: string
  currency: string
  period_start: string
  period_end: string
  recorded_at: string
}

interface DashboardAlert {
  id: string
  rule: string
  metric: string
  severity: string
  status: string
  created_at: string
}

interface Metric {
  id: string
  name: string
  metric_type: string
}

const SEVERITY_COLOR: Record<string, 'cyan' | 'amber' | 'red' | 'zinc'> = {
  info: 'cyan',
  warning: 'amber',
  critical: 'red',
}

const STATUS_COLOR: Record<string, 'red' | 'amber' | 'green' | 'zinc'> = {
  active: 'red',
  acknowledged: 'amber',
  resolved: 'green',
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Token ${token}` } : {}
}

export default function DashboardOverviewPage() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [revenueSnapshots, setRevenueSnapshots] = useState<RevenueSnapshot[]>([])
  const [alerts, setAlerts] = useState<DashboardAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const headers = authHeaders()
    Promise.all([
      fetch('/api/dashboard/metrics/', { headers }).then((r) => r.json()),
      fetch('/api/dashboard/alerts/', { headers }).then((r) => r.json()),
    ])
      .then(([metricsData, alertsData]) => {
        const metricList: Metric[] = metricsData.results ?? metricsData
        setMetrics(metricList)
        setAlerts(alertsData.results ?? alertsData)

        const revenueMetric = metricList.find((m) => m.metric_type === 'revenue')
        if (revenueMetric) {
          const end = new Date().toISOString().slice(0, 10)
          const start = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
          return fetch(
            `/api/dashboard/metrics/${revenueMetric.id}/series/?start_date=${start}&end_date=${end}`,
            { headers },
          ).then((r) => r.json())
        }
        return null
      })
      .then((seriesData) => {
        if (seriesData?.revenue_snapshots) {
          setRevenueSnapshots(seriesData.revenue_snapshots)
        }
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const latestRevenue = revenueSnapshots.length
    ? `$${Number(revenueSnapshots[revenueSnapshots.length - 1].amount).toLocaleString()}`
    : '-'

  const activeAlertCount = alerts.filter((a) => a.status === 'active').length
  const chartData = revenueSnapshots.map((s) => ({
    period: s.period_start,
    amount: Number(s.amount),
  }))

  return (
    <div className="flex flex-col gap-10">
      <div>
        <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-2">
          Ops Overview
        </Heading>
        <Text>Business operations summary.</Text>
      </div>

      {loading && <Text className="animate-pulse">Loading dashboard...</Text>}
      {error && <Text className="text-red-400">Failed to load data: {error}</Text>}

      {!loading && !error && (
        <>
          <PageSection heading="Key Metrics">
            <KpiGrid>
              <KpiCard label="Latest Revenue" value={latestRevenue} trend="neutral" />
              <KpiCard
                label="Active Metrics"
                value={String(metrics.length)}
                trend="neutral"
              />
              <KpiCard
                label="Active Alerts"
                value={String(activeAlertCount)}
                trend={activeAlertCount > 0 ? 'down' : 'neutral'}
              />
            </KpiGrid>
          </PageSection>

          {chartData.length > 0 && (
            <PageSection heading="30-Day Revenue Trend">
              <ChartContainer height={280}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="period" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#0f172a', border: '1px solid #1e293b' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="amount"
                      stroke="#00f0ff"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </PageSection>
          )}

          <PageSection heading="Recent Alerts">
            {alerts.length === 0 ? (
              <Text>No alerts found.</Text>
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeader>Severity</TableHeader>
                    <TableHeader>Status</TableHeader>
                    <TableHeader>Created</TableHeader>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alerts.slice(0, 10).map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>
                        <Badge color={SEVERITY_COLOR[alert.severity] ?? 'zinc'}>
                          {alert.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge color={STATUS_COLOR[alert.status] ?? 'zinc'}>
                          {alert.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(alert.created_at).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </PageSection>
        </>
      )}
    </div>
  )
}
