import clsx from 'clsx'

type Trend = 'up' | 'down' | 'neutral'

type KpiCardProps = {
  label: string
  value: string
  delta?: string
  trend?: Trend
  className?: string
}

export function KpiCard({ label, value, delta, trend = 'neutral', className }: KpiCardProps) {
  const trendColor =
    trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-zinc-400'
  return (
    <div
      className={clsx(
        'rounded-xl border border-cyber-border bg-cyber-surface p-6 flex flex-col gap-2',
        className,
      )}
    >
      <span className="text-sm/5 font-medium text-text-muted uppercase tracking-wider">
        {label}
      </span>
      <span className="text-3xl font-semibold text-text-primary">{value}</span>
      {delta && <span className={clsx('text-sm/5 font-medium', trendColor)}>{delta}</span>}
    </div>
  )
}
