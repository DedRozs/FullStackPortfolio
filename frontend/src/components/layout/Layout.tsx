import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { StackedLayout } from '../catalyst-ui-kit/typescript/stacked-layout'
import { Navbar, NavbarItem, NavbarLabel, NavbarSection } from '../catalyst-ui-kit/typescript/navbar'
import { Link } from '../catalyst-ui-kit/typescript/link'
import brandLogo from '../../assets/Joseph Prince Logo.png'
import Footer from './Footer'

const NAV_LINKS = [
  { href: '/', label: 'Home', end: true },
  { href: '/projects', label: 'Projects' },
  { href: '/ai', label: 'AI Assistant' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
]

export default function Layout() {
  const location = useLocation()

  useEffect(() => {
    document.querySelector('main')?.scrollTo(0, 0)
  }, [location.pathname])

  const isActive = (href: string, end?: boolean) =>
    end ? location.pathname === href : location.pathname.startsWith(href)

  const hideFooter = location.pathname === '/ai'

  return (
    <StackedLayout
      navbar={
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center w-full">
          <Link href="/" className="flex items-center mr-6">
            <img
              src={brandLogo}
              alt="Joseph Prince"
              className="h-10 w-auto drop-shadow-[0_0_8px_rgba(0,255,255,0.6)]"
            />
          </Link>
          <div className="hidden sm:flex flex-1">
            <Navbar>
              <NavbarSection>
                {NAV_LINKS.map(({ href, label, end }) => (
                  <NavbarItem
                    key={href}
                    href={href}
                    current={isActive(href, end)}
                    className="font-display tracking-wider uppercase"
                  >
                    <NavbarLabel>{label}</NavbarLabel>
                  </NavbarItem>
                ))}
              </NavbarSection>
            </Navbar>
          </div>
        </div>
      }
      sidebar={
        <nav className="flex flex-col gap-1 px-4 py-4">
          {NAV_LINKS.map(({ href, label, end }) => (
            <NavbarItem
              key={href}
              href={href}
              className={`font-display tracking-wider uppercase${isActive(href, end) ? ' text-neon-cyan' : ''}`}
            >
              <NavbarLabel>{label}</NavbarLabel>
            </NavbarItem>
          ))}
        </nav>
      }
      footer={hideFooter ? undefined : <Footer />}
    >
      <Outlet />
    </StackedLayout>
  )
}
