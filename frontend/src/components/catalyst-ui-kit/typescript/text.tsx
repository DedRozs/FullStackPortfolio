import { twMerge } from 'tailwind-merge'
import { Link } from './link'

export function Text({ className, ...props }: React.ComponentPropsWithoutRef<'p'>) {
  return (
    <p
      data-slot="text"
      {...props}
      className={twMerge('text-base/6 text-text-muted sm:text-sm/6', className)}
    />
  )
}

export function TextLink({ className, ...props }: React.ComponentPropsWithoutRef<typeof Link>) {
  return (
    <Link
      {...props}
      className={twMerge(
        'text-text-primary underline decoration-text-primary/50 data-hover:decoration-text-primary',
        className,
      )}
    />
  )
}

export function Strong({ className, ...props }: React.ComponentPropsWithoutRef<'strong'>) {
  return <strong {...props} className={twMerge('font-medium text-text-primary', className)} />
}

export function Code({ className, ...props }: React.ComponentPropsWithoutRef<'code'>) {
  return (
    <code
      {...props}
      className={twMerge(
        'rounded-sm border border-cyber-border bg-cyber-elevated px-0.5 text-sm font-medium text-text-primary sm:text-[0.8125rem]',
        className,
      )}
    />
  )
}
