import { useEffect } from 'react'
import { useLocation, useNavigate, Outlet } from 'react-router-dom'
import { SidebarLayout } from '../catalyst-ui-kit/typescript/sidebar-layout'
import {
  Sidebar,
  SidebarBody,
  SidebarDivider,
  SidebarFooter,
  SidebarHeader,
  SidebarHeading,
  SidebarItem,
  SidebarSection,
} from '../catalyst-ui-kit/typescript/sidebar'
import { Navbar, NavbarItem, NavbarLabel } from '../catalyst-ui-kit/typescript/navbar'
import { Link } from '../catalyst-ui-kit/typescript/link'
import { isStaff, clearAuth } from '../../lib/auth'
import { useToast } from '../tailwind-components/simple-notification'
import { TOAST_KEY } from '../StaffRoute'
import brandLogo from '../../assets/Joseph Prince Logo.png'

const PORTAL_NAV = [
  { href: '/portal', label: 'Dashboard', end: true },
  { href: '/portal/files', label: 'Files' },
  { href: '/portal/messages', label: 'Messages' },
]

export default function PortalLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { showToast } = useToast()

  useEffect(() => {
    const raw = sessionStorage.getItem(TOAST_KEY)
    if (raw) {
      sessionStorage.removeItem(TOAST_KEY)
      try {
        const { title, message, variant } = JSON.parse(raw)
        showToast(title, message, variant)
      } catch {
        // malformed entry - ignore
      }
    }
  }, [])

  const isActive = (href: string, end?: boolean) =>
    end ? location.pathname === href : location.pathname.startsWith(href)

  function handleSignOut() {
    clearAuth()
    navigate('/portal/login')
  }

  const sidebar = (
    <Sidebar>
      <SidebarHeader>
        <Link href="/" className="flex items-center gap-3 px-2 py-1">
          <img
            src={brandLogo}
            alt="Joseph Prince"
            className="h-8 w-auto drop-shadow-[0_0_6px_rgba(0,255,255,0.6)]"
          />
          <span className="font-display text-xs tracking-wider uppercase text-neon-magenta">
            Client Portal
          </span>
        </Link>
      </SidebarHeader>

      <SidebarBody>
        <SidebarSection>
          {PORTAL_NAV.map(({ href, label, end }) => (
            <SidebarItem key={href} href={href} current={isActive(href, end)}>
              {label}
            </SidebarItem>
          ))}
        </SidebarSection>
        {isStaff() && (
          <>
            <SidebarDivider />
            <SidebarSection>
              <SidebarHeading>Switch App</SidebarHeading>
              <SidebarItem href="/dashboard">Ops Dashboard</SidebarItem>
              <SidebarItem href="/automations">Automations</SidebarItem>
            </SidebarSection>
          </>
        )}
      </SidebarBody>

      <SidebarFooter>
        <SidebarSection>
          <SidebarItem href="/">Back to Portfolio</SidebarItem>
          <SidebarItem onClick={handleSignOut}>Sign Out</SidebarItem>
        </SidebarSection>
      </SidebarFooter>
    </Sidebar>
  )

  const navbar = (
    <Navbar>
      <NavbarItem href="/portal" current={isActive('/portal', true)}>
        <NavbarLabel className="font-display tracking-wider uppercase">Dashboard</NavbarLabel>
      </NavbarItem>
      <NavbarItem href="/portal/files" current={isActive('/portal/files')}>
        <NavbarLabel className="font-display tracking-wider uppercase">Files</NavbarLabel>
      </NavbarItem>
      <NavbarItem href="/portal/messages" current={isActive('/portal/messages')}>
        <NavbarLabel className="font-display tracking-wider uppercase">Messages</NavbarLabel>
      </NavbarItem>
    </Navbar>
  )

  return (
    <SidebarLayout sidebar={sidebar} navbar={navbar}>
      <Outlet />
    </SidebarLayout>
  )
}
