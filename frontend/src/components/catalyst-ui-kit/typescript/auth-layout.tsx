import type React from 'react'

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh flex-col p-2">
      <div className="flex grow items-center justify-center p-6 lg:rounded-lg lg:bg-cyber-surface lg:p-10 lg:ring-1 lg:ring-cyber-border">
        {children}
      </div>
    </main>
  )
}
