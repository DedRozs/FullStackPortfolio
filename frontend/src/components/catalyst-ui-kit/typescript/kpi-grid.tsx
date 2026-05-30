import clsx from 'clsx'

type KpiGridProps = {
  children: React.ReactNode
  className?: string
}

export function KpiGrid({ children, className }: KpiGridProps) {
  return (
    <div className={clsx('grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3', className)}>
      {children}
    </div>
  )
}
