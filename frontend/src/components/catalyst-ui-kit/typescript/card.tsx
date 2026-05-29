import clsx from 'clsx'
import React from 'react'
import { Link } from './link'

const variants = {
  surface: 'bg-cyber-surface',
  elevated: 'bg-cyber-elevated',
} as const

const accents = {
  cyan: 'hover:border-neon-cyan hover:border-glow-cyan',
  magenta: 'hover:border-neon-magenta hover:border-glow-magenta',
  none: '',
} as const

type Variant = keyof typeof variants
type Accent = keyof typeof accents

type CardOwnProps = {
  variant?: Variant
  accent?: Accent
  /** Remove default padding when using CardHeader / CardBody / CardFooter sub-components */
  flush?: boolean
  className?: string
  children?: React.ReactNode
}

type CardProps = CardOwnProps &
  (
    | ({ href?: never } & Omit<React.ComponentPropsWithoutRef<'div'>, keyof CardOwnProps>)
    | ({ href: string } & Omit<React.ComponentPropsWithoutRef<typeof Link>, keyof CardOwnProps | 'href'>)
  )

export function Card({
  variant = 'surface',
  accent = 'cyan',
  flush = false,
  className,
  children,
  ...props
}: CardProps) {
  const base = clsx(
    'flex flex-col h-full rounded-xl border border-cyber-border transition-all duration-300',
    variants[variant],
    accents[accent],
    // href cards lift on hover; plain divs stay flat unless overridden
    'href' in props && typeof props.href === 'string' && 'hover:-translate-y-1',
    !flush && 'p-6',
    className
  )

  if ('href' in props && typeof props.href === 'string') {
    const { href, ...rest } = props as { href: string } & React.ComponentPropsWithoutRef<typeof Link>
    return (
      <Link href={href} {...rest} className={base}>
        {children}
      </Link>
    )
  }

  return (
    <div {...(props as React.ComponentPropsWithoutRef<'div'>)} className={base}>
      {children}
    </div>
  )
}

export function CardHeader({ className, ...props }: React.ComponentPropsWithoutRef<'div'>) {
  return (
    <div
      data-slot="header"
      {...props}
      className={clsx(className, 'flex flex-col gap-1.5 px-6 pt-6 pb-4')}
    />
  )
}

export function CardBody({ className, ...props }: React.ComponentPropsWithoutRef<'div'>) {
  return (
    <div
      data-slot="body"
      {...props}
      className={clsx(className, 'flex flex-1 flex-col justify-center gap-4 px-6 py-4')}
    />
  )
}

export function CardFooter({ className, ...props }: React.ComponentPropsWithoutRef<'div'>) {
  return (
    <div
      data-slot="footer"
      {...props}
      className={clsx(className, 'flex flex-wrap items-center justify-center gap-2 border-t border-cyber-border px-6 pt-4 pb-6')}
    />
  )
}

export function CardTitle({ className, ...props }: React.ComponentPropsWithoutRef<'h3'>) {
  return (
    <h3
      {...props}
      className={clsx(className, 'font-display text-sm font-bold tracking-widest text-text-primary uppercase')}
    />
  )
}

export function CardDescription({ className, ...props }: React.ComponentPropsWithoutRef<'p'>) {
  return (
    <p
      {...props}
      className={clsx(className, 'text-text-muted text-sm leading-relaxed')}
    />
  )
}
