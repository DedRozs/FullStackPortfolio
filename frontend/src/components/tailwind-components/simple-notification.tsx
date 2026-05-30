import { createContext, useCallback, useContext, useState } from 'react'
import { Transition } from '@headlessui/react'

// ---------------------------------------------------------------------------
// Icons (inline SVG - no heroicons dependency required)
// ---------------------------------------------------------------------------

function IconWarning() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6 text-neon-magenta" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  )
}

function IconSuccess() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6 text-neon-cyan" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  )
}

function IconClose() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="size-5" aria-hidden="true">
      <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Toast component
// ---------------------------------------------------------------------------

export type ToastVariant = 'warning' | 'success'

interface ToastProps {
  show: boolean
  onClose: () => void
  title: string
  message?: string
  variant?: ToastVariant
}

export function Toast({ show, onClose, title, message, variant = 'warning' }: ToastProps) {
  const accentClass = variant === 'success' ? 'border-l-neon-cyan' : 'border-l-neon-magenta'

  return (
    <div aria-live="assertive" className="pointer-events-none fixed inset-0 flex items-end px-4 py-6 sm:items-start sm:p-6 z-50">
      <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
        <Transition show={show}>
          <div
            className={[
              'pointer-events-auto w-full max-w-sm rounded-lg border border-cyber-border border-l-2',
              accentClass,
              'bg-cyber-elevated shadow-lg',
              'transition data-closed:opacity-0',
              'data-enter:transform data-enter:duration-300 data-enter:ease-out',
              'data-closed:data-enter:translate-y-2 data-closed:data-enter:sm:translate-x-2 data-closed:data-enter:sm:translate-y-0',
              'data-leave:duration-100 data-leave:ease-in',
            ].join(' ')}
          >
            <div className="p-4">
              <div className="flex items-start">
                <div className="shrink-0">
                  {variant === 'success' ? <IconSuccess /> : <IconWarning />}
                </div>
                <div className="ml-3 w-0 flex-1 pt-0.5">
                  <p className="text-sm font-medium text-text-primary">{title}</p>
                  {message && <p className="mt-1 text-sm text-text-muted">{message}</p>}
                </div>
                <div className="ml-4 flex shrink-0">
                  <button
                    type="button"
                    onClick={onClose}
                    className="inline-flex rounded-md text-text-muted hover:text-neon-cyan focus:outline-2 focus:outline-offset-2 focus:outline-neon-cyan"
                  >
                    <span className="sr-only">Close</span>
                    <IconClose />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Context + Provider
// ---------------------------------------------------------------------------

interface ToastState {
  show: boolean
  title: string
  message?: string
  variant: ToastVariant
}

interface ToastContextValue {
  showToast: (title: string, message?: string, variant?: ToastVariant) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ToastState>({
    show: false,
    title: '',
    variant: 'warning',
  })

  const showToast = useCallback((title: string, message?: string, variant: ToastVariant = 'warning') => {
    setState({ show: true, title, message, variant })
  }, [])

  function handleClose() {
    setState((s) => ({ ...s, show: false }))
  }

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Toast
        show={state.show}
        onClose={handleClose}
        title={state.title}
        message={state.message}
        variant={state.variant}
      />
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside ToastProvider')
  return ctx
}
