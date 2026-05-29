import { useEffect, useRef } from 'react'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { SKILLS } from '../data/skills'

const CAREER_MILESTONES = [
  {
    title: 'Chief Technology Officer',
    org: 'Sports Thread',
    period: '2023 – Present',
    description:
      'Own architecture, scalability, and security across the full platform. Set technical direction, lead engineering execution, and remain hands-on writing and reviewing production code.',
  },
  {
    title: 'VP of Engineering',
    org: 'Sports Thread',
    period: '2022 – 2023',
    description:
      'Scaled the platform from early-stage to production-grade. Led backend infrastructure overhaul and introduced Clean Architecture across the Django codebase.',
  },
  {
    title: 'Director of Engineering',
    org: 'Sports Thread',
    period: '2021 – 2022',
    description:
      'First engineering leadership role. Built initial REST API layer, established CI/CD practices, and took ownership of Google Cloud Platform deployments.',
  },
]

const CREDENTIALS = [
  {
    credential: 'B.S. Computer Science (Data Science)',
    institution: 'Colorado Technical University',
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
        <p
          className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3 animate-fade-in-up"
          style={{ animationDelay: '0s' }}
        >
          CTO &amp; Full-Stack Developer
        </p>
        <h1
          className="font-display text-4xl sm:text-5xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          About
        </h1>
        <p
          className="text-text-muted text-lg max-w-2xl leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Four years growing from Director to CTO at Sports Thread - hands-on throughout,
          writing production code while owning architecture, scalability, and security.
        </p>
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
        <div className="max-w-3xl mx-auto px-6 space-y-6 text-text-muted leading-relaxed">
          <p>
            Joseph Prince is the Chief Technology Officer at Sports Thread, where he leads
            technology strategy, platform development, and engineering execution. Over 4+
            years he has grown from Director to VP to CTO - hands-on throughout, writing and
            reviewing production code while owning architecture, scalability, and security.
          </p>
          <p>
            Proficient in Python and Django on the backend, React and TypeScript on the
            frontend, and Google Cloud Platform for deployment. Holds a B.S. in Computer
            Science (Data Science) from Colorado Technical University and certifications in
            Scrum (CSM, CSPO, CSD).
          </p>
          <p>
            Available for consulting engagements. Focused on clean architecture,
            maintainable code, and AI integration.
          </p>
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
            <p className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Experience
            </p>
            <h2 className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Career
            </h2>
          </div>

          <div className="flex flex-col gap-6" ref={careerRef}>
            {CAREER_MILESTONES.map((milestone, i) => (
              <div
                key={milestone.title}
                data-delay={i * 100}
                className="reveal grid sm:grid-cols-[200px_1fr] gap-4 sm:gap-8 items-start"
              >
                <div className="sm:text-right">
                  <p className="font-display text-sm font-bold text-neon-cyan tracking-wide">
                    {milestone.period}
                  </p>
                  <p className="text-text-muted text-xs font-display tracking-widest uppercase mt-1">
                    {milestone.org}
                  </p>
                </div>
                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-6 py-5 hover:border-neon-cyan/50 transition-colors">
                  <h3 className="font-display text-base font-bold text-text-primary tracking-wide mb-2">
                    {milestone.title}
                  </h3>
                  <p className="text-text-muted text-sm leading-relaxed">
                    {milestone.description}
                  </p>
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
            <p className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Technologies
            </p>
            <h2 className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Skills
            </h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" ref={skillsRef}>
            {SKILLS.map((skill, i) => (
              <div
                key={skill}
                data-delay={i * 50}
                className="reveal bg-cyber-elevated border border-cyber-border rounded-xl px-4 py-3 text-center hover:border-neon-cyan/50 transition-colors"
              >
                <span className="text-sm font-display tracking-wider text-text-primary uppercase">
                  {skill}
                </span>
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
            <p className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Credentials
            </p>
            <h2 className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              Education
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
            {CREDENTIALS.map((item) => (
              <div
                key={item.credential}
                className="bg-cyber-elevated border border-cyber-border rounded-xl px-6 py-5 hover:border-neon-cyan/50 transition-colors"
              >
                <p className="font-display text-sm font-bold text-text-primary tracking-wide mb-1">
                  {item.credential}
                </p>
                <p className="text-text-muted text-xs font-display tracking-widest uppercase">
                  {item.institution}
                </p>
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
          <p className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
            Available Now
          </p>
          <h2 className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6">
            Get In Touch
          </h2>
          <p className="text-text-muted text-base leading-relaxed mb-8">
            Open to consulting engagements and senior engineering roles. If you have
            something interesting to build, let's talk.
          </p>
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
