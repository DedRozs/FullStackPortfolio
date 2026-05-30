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
import { clearAuth } from '../../lib/auth'
import brandLogo from '../../assets/Joseph Prince Logo.png'

const DASHBOARD_NAV = [
  { href: '/dashboard', label: 'Overview', end: true },
  { href: '/dashboard/metrics', label: 'Metrics' },
  { href: '/dashboard/alerts', label: 'Alerts' },
]

export default function DashboardLayout() {
  const location = useLocation()
  const navigate = useNavigate()

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
            Ops Dashboard
          </span>
        </Link>
      </SidebarHeader>

      <SidebarBody>
        <SidebarSection>
          {DASHBOARD_NAV.map(({ href, label, end }) => (
            <SidebarItem key={href} href={href} current={isActive(href, end)}>
              {label}
            </SidebarItem>
          ))}
        </SidebarSection>
        <SidebarDivider />
        <SidebarSection>
          <SidebarHeading>Switch App</SidebarHeading>
          <SidebarItem href="/portal">Client Portal</SidebarItem>
          <SidebarItem href="/automations">Automations</SidebarItem>
        </SidebarSection>
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
      <NavbarItem href="/dashboard" current={isActive('/dashboard', true)}>
        <NavbarLabel className="font-display tracking-wider uppercase">Overview</NavbarLabel>
      </NavbarItem>
      <NavbarItem href="/dashboard/metrics" current={isActive('/dashboard/metrics')}>
        <NavbarLabel className="font-display tracking-wider uppercase">Metrics</NavbarLabel>
      </NavbarItem>
      <NavbarItem href="/dashboard/alerts" current={isActive('/dashboard/alerts')}>
        <NavbarLabel className="font-display tracking-wider uppercase">Alerts</NavbarLabel>
      </NavbarItem>
    </Navbar>
  )

  return (
    <SidebarLayout sidebar={sidebar} navbar={navbar}>
      <Outlet />
    </SidebarLayout>
  )
}
