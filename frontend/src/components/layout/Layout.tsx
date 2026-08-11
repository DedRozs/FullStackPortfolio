import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { StackedLayout } from '../catalyst-ui-kit/typescript/stacked-layout'
import { Navbar, NavbarItem, NavbarLabel, NavbarSection } from '../catalyst-ui-kit/typescript/navbar'
import { Link } from '../catalyst-ui-kit/typescript/link'
import brandLogo from '../../assets/Joseph Prince Logo.png'
import Footer from './Footer'

/* Primary navigation only.
   The demo apps (/portal, /dashboard, /automations) deliberately live off this
   list: they are auth-gated, so a visitor clicking them from the top bar hits a
   login wall. They are reachable from the projects page and the home page demo
   strip, which is the context where they make sense. */
const NAV_LINKS = [
  { href: '/', label: 'Home', end: true },
  { href: '/projects', label: 'Projects' },
  { href: '/about', label: 'About' },
  { href: '/blog', label: 'Blog' },
  { href: '/ai', label: 'AI Assistant' },
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
          {/* shrink-0 on both the link and the image: as flex children they
              default to flex-shrink:1, so a crowded navbar squeezes the image
              width while h-10 pins its height. With object-fit:fill that
              stretches the wordmark - it was rendering 57% narrower than its
              native 3.38 aspect. object-contain is the backstop. */}
          <Link href="/" className="flex items-center mr-6 shrink-0">
            <img
              src={brandLogo}
              alt="Joseph Prince"
              className="h-10 w-auto shrink-0 object-contain drop-shadow-[0_0_8px_rgba(0,255,255,0.6)]"
            />
          </Link>
          {/* lg, not sm: logo (135) + gap (24) + six nav items (620) + page
              padding (48) needs ~830px. At the sm breakpoint the bar clipped
              its own trailing links. Must stay in step with the menu-button
              breakpoint in stacked-layout.tsx. */}
          <div className="hidden lg:flex flex-1">
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
