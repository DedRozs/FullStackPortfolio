import clsx from 'clsx'

type ChartContainerProps = {
  children: React.ReactNode
  height?: number
  className?: string
}

export function ChartContainer({ children, height = 300, className }: ChartContainerProps) {
  return (
    <div
      className={clsx('rounded-xl border border-cyber-border bg-cyber-surface p-6', className)}
      style={{ height }}
    >
      {children}
    </div>
  )
}
