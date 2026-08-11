import { useEffect, useRef } from 'react'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../components/catalyst-ui-kit/typescript/text'
import { SKILL_GROUPS } from '../data/skills'
import headshot from '../assets/Headshot.png'

/* Written from what was actually shipped in each period rather than from job
   descriptions. Same disclosure rule as the projects page: no vendor, partner
   or client names, and no commercial figures. */
const CAREER_MILESTONES = [
  {
    title: 'Chief Technology Officer',
    org: 'Sports Thread',
    period: 'Jan 2026 – Present',
    description:
      'Own architecture, scalability and security across the platform, and provide the engineering oversight of the outsourced vendor team that maintains its core. Authored a cost-engineering assessment that audited their codebase and reclassified a misdiagnosed infrastructure issue, and a technical proposal analysing four independent authentication systems across roughly 350 routes - accepted and implemented. Still shipping: 2026 is my highest-output year of authored code to date.',
  },
  {
    title: 'VP of Software Development',
    org: 'Sports Thread',
    period: 'Nov 2023 – Jan 2026',
    description:
      'Architected and wrote the platform that fronts our partner integrations and handles coach credentialing end to end - registration, waivers, payment, screening and roster provisioning. Built the multi-tenant recruiting CRM backend serving 600+ tenant organisations, and hired and now manage the frontend developer who builds against those APIs.',
  },
  {
    title: 'Director of Software Engineering',
    org: 'Sports Thread',
    period: 'Jun 2022 – Nov 2023',
    description:
      'Built the age-verification and compliance platform that is still the operational backbone of event certification, reimplementing verification rules from a vendor-maintained service in another language and holding them to behavioural parity. Set the architectural standard - Clean Architecture with a framework-free domain layer - that the later systems were built on.',
  },
  {
    title: 'Marketing Manager',
    org: 'Sports Thread',
    period: 'Jan 2022 – Jun 2022',
    description:
      'Hired into a non-technical marketing role and started writing code against the company’s real problems within weeks. The title caught up six months later - the work came first. The marketing half is not incidental: it is why I evaluate technical decisions against business outcomes rather than treating them as separate questions.',
  },
]

/* `note` gives an entry context a bare credential line can't carry - the
   marketing immersion is the origin of the career pivot, not a stray cert. */
const CREDENTIALS = [
  {
    credential: 'B.S. Computer Science',
    institution: 'Colorado Technical University',
    note: 'Completed 2026, while serving as VP and then CTO.',
  },
  {
    credential: 'Digital Marketing Immersion',
    institution: 'Thinkful',
    note: 'Where the career started - and why business context drives the engineering.',
  },
  {
    credential: 'Certified Scrum Master (CSM)',
    institution: 'Scrum Alliance',
  },
  {
    credential: 'Certified Scrum Product Owner (CSPO)',
    institution: 'Scrum Alliance',
  },
  {
    credential: 'Certified Scrum Developer (CSD)',
    institution: 'Scrum Alliance',
  },
]

export default function AboutPage() {
  const careerRef = useRef<HTMLDivElement>(null)
  const skillsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const containers = [careerRef.current, skillsRef.current].filter(Boolean) as HTMLDivElement[]
    if (containers.length === 0) return

    const elements = containers.flatMap((c) =>
      Array.from(c.querySelectorAll<HTMLElement>('.reveal')),
    )
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target as HTMLElement
            const delay = el.dataset.delay ?? '0'
            el.style.transitionDelay = `${delay}ms`
            el.classList.add('is-visible')
            observer.unobserve(el)
          }
        })
      },
      { threshold: 0.08 },
    )
    elements.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <>
      {/* Hero */}
      <section className="scanlines relative pt-20 pb-10 flex flex-col items-center text-center px-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,27,114,0.4) 0%, transparent 70%)',
          }}
        />
        <Text
          className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3 animate-fade-in-up"
          style={{ animationDelay: '0s' }}
        >
          CTO &middot; Staff-Level Backend Engineer
        </Text>
        <Heading
          level={1}
          className="font-display text-4xl sm:text-5xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          About
        </Heading>
        <Text
          className="text-lg max-w-2xl leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Over four years at Sports Thread - from Marketing Manager to Chief Technology Officer,
          fully remote and hands-on throughout, writing production code while owning architecture,
          scalability, and security.
        </Text>

        <div
          className="flex flex-wrap gap-4 mt-8 justify-center animate-fade-in-up"
          style={{ animationDelay: '0.3s' }}
        >
          <a
            href="/resume"
            className="px-5 py-2.5 text-xs font-display tracking-widest uppercase text-neon-cyan border border-neon-cyan/50 rounded hover:border-neon-cyan hover:glow-cyan transition-all"
          >
            View R&eacute;sum&eacute; &rarr;
          </a>
        </div>
      </section>

      {/* Bio */}
      <section className="relative overflow-hidden py-20">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,255,255,0.04) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex flex-col sm:flex-row gap-10 items-start">
            {/* Headshot */}
            <div className="flex-shrink-0 mx-auto sm:mx-0">
              <div className="relative w-48 h-48 sm:w-56 sm:h-56 rounded-2xl overflow-hidden border-2 border-neon-cyan/60 shadow-[0_0_28px_rgba(0,255,255,0.2)]">
                <img
                  src={headshot}
                  alt="Joseph Prince"
                  className="w-full h-full object-cover object-top grayscale"
                />
                <div
                  className="absolute inset-0 pointer-events-none"
                  aria-hidden="true"
                  style={{ background: 'rgba(0,255,255,0.06)', mixBlendMode: 'screen' }}
                />
              </div>
            </div>

            {/* Bio text */}
            <div className="space-y-6 text-text-muted leading-relaxed">
              <Text>
                Joseph Prince is the Chief Technology Officer at Sports Thread, a youth sports
                technology platform. He joined in 2022 as a non-technical marketing manager and
                was writing code against the company&apos;s own problems within weeks; the title
                caught up six months later. Marketing Manager to Director to VP to CTO in four
                years.
              </Text>
              <Text>
                Most engineering leaders stop writing code somewhere on that path.{' '}
                <span className="text-neon-cyan">
                  His authored commit volume has increased every year instead
                </span>
                {' '}- he is the primary author of four production backend systems, manages a
                frontend developer, and provides the engineering oversight of an outsourced
                vendor team maintaining the core platform.
              </Text>
              <Text>
                Python and Django on the backend, React and TypeScript on the frontend, deployed
                across GCP and AWS. Focused on clean architecture, systems that stay maintainable
                years later, and AI integration that works in production rather than in a demo.
              </Text>
              <Text>
                Open to senior engineering roles and consulting engagements.
              </Text>
            </div>
          </div>
        </div>
      </section>

      {/* Career timeline */}
      <section className="relative overflow-hidden py-20">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(59,27,114,0.35) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Experience
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Career
            </Heading>
          </div>

          <div className="flex flex-col gap-6" ref={careerRef}>
            {CAREER_MILESTONES.map((milestone, i) => (
              <div
                key={milestone.title}
                data-delay={i * 100}
                className="reveal grid sm:grid-cols-[200px_1fr] gap-4 sm:gap-8 items-start"
              >
                <div className="sm:text-right">
                  <Text className="font-display text-sm font-bold text-neon-cyan tracking-wide">
                    {milestone.period}
                  </Text>
                  <Text className="text-xs font-display tracking-widest uppercase mt-1">
                    {milestone.org}
                  </Text>
                </div>
                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-6 py-5 hover:border-neon-cyan/50 transition-colors">
                  <Heading level={3} className="font-display text-base font-bold text-text-primary tracking-wide mb-2">
                    {milestone.title}
                  </Heading>
                  <Text className="text-sm leading-relaxed">
                    {milestone.description}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Skills */}
      <section className="relative overflow-hidden py-20">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 100%, rgba(0,255,255,0.06) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Technologies
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Skills
            </Heading>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5" ref={skillsRef}>
            {SKILL_GROUPS.map((group, i) => (
              <div
                key={group.area}
                data-delay={i * 80}
                className="reveal bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-5 hover:border-neon-cyan/50 transition-colors"
              >
                <Text className="text-[10px] font-display tracking-widest uppercase text-neon-cyan/70 mb-3">
                  {group.area}
                </Text>
                <div className="flex flex-wrap gap-1.5">
                  {group.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2 py-1 text-[11px] font-display tracking-wide text-text-muted border border-cyber-border rounded uppercase"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Education & certifications */}
      <section className="relative overflow-hidden py-20">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(59,27,114,0.2) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Credentials
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Education
            </Heading>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
            {CREDENTIALS.map((item) => (
              <div
                key={item.credential}
                className="bg-cyber-elevated border border-cyber-border rounded-xl px-6 py-5 hover:border-neon-cyan/50 transition-colors"
              >
                <Text className="font-display text-sm font-bold text-text-primary tracking-wide mb-1">
                  {item.credential}
                </Text>
                <Text className="text-xs font-display tracking-widest uppercase">
                  {item.institution}
                </Text>
                {item.note && (
                  <Text className="text-xs leading-relaxed mt-2 text-text-muted/80">
                    {item.note}
                  </Text>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden py-24 text-center">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 60% 80% at 50% 100%, rgba(0,255,255,0.08) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-xl mx-auto px-6">
          <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
            Available Now
          </Text>
          <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6">
            Get In Touch
          </Heading>
          <Text className="text-base leading-relaxed mb-8">
            Open to consulting engagements and senior engineering roles. If you have
            something interesting to build, let's talk.
          </Text>
          <div className="flex flex-wrap gap-4 justify-center">
            <Button color="neon-cyan" href="/contact" className="font-display tracking-widest uppercase">
              Contact Me
            </Button>
            <Button color="neon-cyan-outline" href="/projects" className="font-display tracking-widest uppercase">
              View Projects
            </Button>
          </div>
        </div>
      </section>
    </>
  )
}
