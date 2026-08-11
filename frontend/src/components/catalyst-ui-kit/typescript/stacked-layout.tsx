'use client'

import * as Headless from '@headlessui/react'
import React, { useState } from 'react'
import { NavbarItem } from './navbar'

// Catalyst ships a two-bar menu glyph whose artwork spans only y=6..14 of a
// 20x20 box - a 1.9:1 content ratio that reads as squashed. This is a
// conventional three-bar hamburger, evenly spaced and filling the box.
function OpenMenuIcon() {
  return (
    <svg data-slot="icon" viewBox="0 0 20 20" aria-hidden="true" fill="currentColor">
      <rect x="2.5" y="4.2" width="15" height="1.6" rx="0.8" />
      <rect x="2.5" y="9.2" width="15" height="1.6" rx="0.8" />
      <rect x="2.5" y="14.2" width="15" height="1.6" rx="0.8" />
    </svg>
  )
}

function CloseMenuIcon() {
  return (
    <svg data-slot="icon" viewBox="0 0 20 20" aria-hidden="true">
      <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
    </svg>
  )
}

function MobileSidebar({ open, close, children }: React.PropsWithChildren<{ open: boolean; close: () => void }>) {
  return (
    <Headless.Dialog open={open} onClose={close} className="lg:hidden">
      <Headless.DialogBackdrop
        transition
        className="fixed inset-0 bg-black/50 transition data-closed:opacity-0 data-enter:duration-300 data-enter:ease-out data-leave:duration-200 data-leave:ease-in"
      />
      <Headless.DialogPanel
        transition
        className="fixed inset-y-0 w-full max-w-80 p-2 transition duration-300 ease-in-out data-closed:-translate-x-full"
      >
        <div className="flex h-full flex-col bg-cyber-surface border border-cyber-border">
          <div className="flex items-center justify-end px-4 pt-3 pb-1">
            <Headless.CloseButton as={NavbarItem} aria-label="Close navigation">
              <CloseMenuIcon />
            </Headless.CloseButton>
          </div>
          {children}
        </div>
      </Headless.DialogPanel>
    </Headless.Dialog>
  )
}

export function StackedLayout({
  navbar,
  sidebar,
  footer,
  children,
}: React.PropsWithChildren<{ navbar: React.ReactNode; sidebar: React.ReactNode; footer?: React.ReactNode }>) {
  let [showSidebar, setShowSidebar] = useState(false)

  return (
    <div className="relative isolate flex h-svh w-full flex-col overflow-hidden bg-cyber-dark print:h-auto print:overflow-visible">
      {/* Sidebar on mobile */}
      <MobileSidebar open={showSidebar} close={() => setShowSidebar(false)}>
        {sidebar}
      </MobileSidebar>

      {/* Navbar */}
      <header className="shrink-0 z-50 flex items-center bg-cyber-surface/90 backdrop-blur border-b border-cyber-border print:hidden">
        <div className="min-w-0 flex-1">{navbar}</div>
        <div className="py-2.5 pr-4 lg:hidden">
          <NavbarItem onClick={() => setShowSidebar(true)} aria-label="Open navigation">
            <OpenMenuIcon />
          </NavbarItem>
        </div>
      </header>

      {/* Content + footer scroll together */}
      <main className="flex-1 overflow-y-auto min-h-0 print:overflow-visible">
        {children}
        {footer}
      </main>
    </div>
  )
}
