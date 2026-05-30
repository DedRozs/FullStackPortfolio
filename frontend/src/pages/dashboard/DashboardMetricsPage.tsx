import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Input } from '../../components/catalyst-ui-kit/typescript/input'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/catalyst-ui-kit/typescript/table'
import { ChartContainer } from '../../components/catalyst-ui-kit/typescript/chart-container'
import { PageSection } from '../../components/catalyst-ui-kit/typescript/page-section'

interface Metric {
  id: string
  name: string
  metric_type: string
  description: string | null
  created_at: string
}

interface RevenueSnapshot {
  id: string
  amount: string
  currency: string
  period_start: string
  period_end: string
}

interface GrowthSnapshot {
  id: string
  new_customers: number
  churned_customers: number
  net_customers: number
  period_start: string
  period_end: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Token ${token}` } : {}
}

function defaultStartDate(): string {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return d.toISOString().slice(0, 10)
}

export default function DashboardMetricsPage() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null)
  const [snapshots, setSnapshots] = useState<RevenueSnapshot[]>([])
  const [growthSnapshots, setGrowthSnapshots] = useState<GrowthSnapshot[]>([])
  const [startDate, setStartDate] = useState(defaultStartDate())
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10))
  const [loading, setLoading] = useState(true)
  const [seriesLoading, setSeriesLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/dashboard/metrics/', { headers: authHeaders() })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setMetrics(data.results ?? data)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  function loadSeries(metric: Metric) {
    setSelectedMetric(metric)
    setSeriesLoading(true)
    setSnapshots([])
    setGrowthSnapshots([])
    fetch(
      `/api/dashboard/metrics/${metric.id}/series/?start_date=${startDate}&end_date=${endDate}`,
      { headers: authHeaders() },
    )
      .then((r) => r.json())
      .then((data) => {
        setSnapshots(data.revenue_snapshots ?? [])
        setGrowthSnapshots(data.growth_snapshots ?? [])
        setSeriesLoading(false)
      })
      .catch(() => setSeriesLoading(false))
  }

  function handleExport() {
    if (!selectedMetric) return
    const url = `/api/dashboard/metrics/${selectedMetric.id}/export/?start_date=${startDate}&end_date=${endDate}`
    window.open(url, '_blank')
  }

  const chartData = selectedMetric?.metric_type === 'customer_growth'
    ? growthSnapshots.map((s) => ({ period: s.period_start, amount: s.net_customers }))
    : snapshots.map((s) => ({ period: s.period_start, amount: Number(s.amount) }))

  const hasData = chartData.length > 0

  return (
    <div className="flex flex-col gap-10">
      <div>
        <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-2">
          Metrics
        </Heading>
        <Text>Browse and analyse tracked business metrics.</Text>
      </div>

      {loading && <Text className="animate-pulse">Loading metrics...</Text>}
      {error && <Text className="text-red-400">Failed to load metrics: {error}</Text>}

      {!loading && !error && (
        <>
          <PageSection heading="All Metrics">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Name</TableHeader>
                  <TableHeader>Type</TableHeader>
                  <TableHeader>Created</TableHeader>
                  <TableHeader>Action</TableHeader>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.map((metric) => (
                  <TableRow key={metric.id}>
                    <TableCell>{metric.name}</TableCell>
                    <TableCell>{metric.metric_type}</TableCell>
                    <TableCell>{new Date(metric.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Button plain onClick={() => loadSeries(metric)}>
                        View Series
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </PageSection>

          {selectedMetric && (
            <PageSection heading={`Series: ${selectedMetric.name}`}>
              <div className="flex flex-wrap items-end gap-4">
                <div className="flex flex-col gap-1">
                  <Text>Start date</Text>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <Text>End date</Text>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
                <Button onClick={() => loadSeries(selectedMetric)}>Refresh</Button>
                <Button outline onClick={handleExport}>
                  Export CSV
                </Button>
              </div>

              {seriesLoading && <Text className="animate-pulse">Loading series...</Text>}

              {!seriesLoading && hasData && (
                <ChartContainer height={280}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <XAxis dataKey="period" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: '#0f172a', border: '1px solid #1e293b' }}
                      />
                      <Bar dataKey="amount" fill="#00f0ff" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              )}

              {!seriesLoading && !hasData && (
                <Text>No snapshots found for this period.</Text>
              )}
            </PageSection>
          )}
        </>
      )}
    </div>
  )
}
