import { useEffect, useRef } from 'react'
import { Badge } from '../components/catalyst-ui-kit/typescript/badge'
import { Card, CardBody, CardFooter, CardHeader, CardTitle } from '../components/catalyst-ui-kit/typescript/card'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../components/catalyst-ui-kit/typescript/text'

const PROJECTS = [
  {
    number: '01',
    title: 'Secure Client Portal',
    pitch:
      'A full-stack portal where companies manage projects, files, deliverables, invoices, and approvals. Demonstrates secure permissioned multi-user workflows - the kind of software companies actually pay developers to build.',
    architectureHighlight:
      'Object-level permissions enforce data isolation per organization without a separate tenancy model. An approval state machine tracks every transition with a full audit trail, making the business process explicit in code.',
    tags: ['Django', 'DRF', 'React', 'GCS', 'SendGrid', 'Django-Q2'],
    accent: 'cyan' as const,
  },
  {
    number: '02',
    title: 'Operations Dashboard',
    pitch:
      'An internal analytics dashboard that turns raw business data into KPIs, charts, filters, and automated alerts. Built to demonstrate executive-facing software beyond CRUD screens.',
    architectureHighlight:
      'Alert evaluation runs as a scheduled Django-Q2 task every 15 minutes, not in the request cycle. Aggregation logic lives in a dedicated service layer - period-over-period deltas and rolling averages are testable without hitting the database.',
    tags: ['Django', 'DRF', 'React', 'Recharts', 'Django-Q2'],
    accent: 'magenta' as const,
  },
  {
    number: '03',
    title: 'Workflow Automation Engine',
    pitch:
      'A lightweight automation system where users define triggers, conditions, and actions - an internal Zapier built for business workflows. The architectural showpiece of the three projects.',
    architectureHighlight:
      'A decorator-based registry decouples trigger types, condition operators, and action handlers from the core engine. Dry-run mode evaluates a full rule and logs every decision without side effects - critical for validating automation logic before going live.',
    tags: ['Django', 'DRF', 'React', 'Twilio', 'SendGrid', 'Django-Q2'],
    accent: 'cyan' as const,
  },
]

const ECOSYSTEM_STEPS = [
  {
    from: 'Client Portal',
    event: 'deliverable.approved',
    to: 'Automation Engine',
    result: 'Email sent + activity logged',
  },
  {
    from: 'Ops Dashboard',
    event: 'metric.threshold_crossed',
    to: 'Automation Engine',
    result: 'SMS alert via Twilio',
  },
]

export default function ProjectsPage() {
  const cardsRef = useRef<HTMLDivElement>(null)
  const ecosystemRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const containers = [cardsRef.current, ecosystemRef.current].filter(Boolean) as HTMLDivElement[]
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
          Full-Stack Portfolio
        </Text>
        <Heading
          level={1}
          className="font-display text-4xl sm:text-5xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          Projects
        </Heading>
        <Text
          className="text-lg max-w-2xl leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Three interconnected Django + React applications built to demonstrate
          production-grade architecture - permissioned APIs, background task processing,
          domain-driven design, and a shared automation layer that ties them together.
        </Text>

        <div
          className="flex items-center gap-3 mt-8 animate-fade-in-up"
          style={{ animationDelay: '0.3s' }}
        >
          <span className="w-2 h-2 rounded-full bg-neon-magenta animate-pulse" />
          <span className="text-neon-magenta text-xs font-display tracking-widest uppercase">
            In Active Development
          </span>
        </div>
      </section>

      {/* Project cards */}
      <section className="relative pt-4 pb-16 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 50% 50%, rgba(0,255,255,0.04) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6 flex flex-col gap-8" ref={cardsRef}>
          {PROJECTS.map((project, i) => (
            <Card
              key={project.title}
              flush
              accent={project.accent}
              data-delay={i * 100}
              className="reveal"
            >
              {/* Top bar with number + status */}
              <div className="flex items-center justify-between px-6 pt-6 pb-0">
                <span className="font-display text-3xl font-bold text-cyber-border select-none">
                  {project.number}
                </span>
                <Badge color="neon-magenta" className="font-display text-[10px] tracking-widest uppercase">
                  In Development
                </Badge>
              </div>

              <CardHeader>
                <CardTitle className="text-neon-cyan text-base">{project.title}</CardTitle>
              </CardHeader>

              <CardBody>
                <Text className="text-sm leading-relaxed">{project.pitch}</Text>

                {/* Architecture callout */}
                <div className="mt-2 border-l-2 border-neon-cyan/40 pl-4">
                  <Text className="text-[10px] font-display tracking-widest uppercase text-neon-cyan/60 mb-1">
                    Architecture Highlight
                  </Text>
                  <Text className="text-sm leading-relaxed">
                    {project.architectureHighlight}
                  </Text>
                </div>
              </CardBody>

              <CardFooter>
                {project.tags.map((tag) => (
                  <span
                    key={tag}
                    className="flex-1 basis-[calc(33%-4px)] px-2 py-1.5 text-xs font-display tracking-wide text-text-muted border border-cyber-border rounded uppercase text-center whitespace-nowrap"
                  >
                    {tag}
                  </span>
                ))}
              </CardFooter>
            </Card>
          ))}
        </div>
      </section>

      {/* Ecosystem section */}
      <section className="relative py-24 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 100%, rgba(59,27,114,0.35) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Connected by Design
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              The Ecosystem
            </Heading>
            <Text className="text-sm max-w-2xl mx-auto mt-4 leading-relaxed">
              The three applications are not isolated demos - they share a common automation
              layer. Events fired in the portal and dashboard are consumed by the workflow
              engine, closing the loop between user action and automated response.
            </Text>
          </div>

          <div className="flex flex-col gap-4" ref={ecosystemRef}>
            {ECOSYSTEM_STEPS.map((step, i) => (
              <div
                key={step.event}
                data-delay={i * 120}
                className="reveal grid sm:grid-cols-[1fr_2fr_1fr] items-center gap-4"
              >
                {/* Source */}
                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-4 text-center">
                  <Text className="text-[10px] font-display tracking-widest uppercase mb-1">
                    Source
                  </Text>
                  <Text className="font-display text-sm font-bold text-text-primary">{step.from}</Text>
                </div>

                {/* Connector: arrow → event label → engine → arrow */}
                <div className="flex flex-col items-center gap-2">
                  <span className="text-[10px] font-mono text-neon-cyan/70 tracking-wide">
                    {step.event}
                  </span>
                  <div className="flex items-center gap-3 w-full">
                    <span className="text-neon-cyan select-none">&#8594;</span>
                    <div className="flex-1 bg-cyber-elevated border border-neon-cyan/30 rounded-xl px-3 py-3 text-center">
                      <p className="font-display text-xs font-bold text-neon-cyan">Automation Engine</p>
                    </div>
                    <span className="text-neon-magenta select-none">&#8594;</span>
                  </div>
                </div>

                {/* Result */}
                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-4 text-center">
                  <Text className="text-[10px] font-display tracking-widest uppercase mb-1">
                    Result
                  </Text>
                  <Text className="font-display text-sm font-bold text-neon-green">{step.result}</Text>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
