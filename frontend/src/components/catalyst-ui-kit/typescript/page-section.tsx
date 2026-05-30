import clsx from 'clsx'

type PageSectionProps = {
  heading?: string
  children: React.ReactNode
  className?: string
}

export function PageSection({ heading, children, className }: PageSectionProps) {
  return (
    <section className={clsx('flex flex-col gap-4', className)}>
      {heading && (
        <h2 className="text-base/7 font-semibold text-text-primary sm:text-sm/6">{heading}</h2>
      )}
      {children}
    </section>
  )
}
