import { useEffect, useRef } from 'react'
import { Badge } from '../components/catalyst-ui-kit/typescript/badge'
import { Card, CardBody, CardFooter, CardHeader, CardTitle } from '../components/catalyst-ui-kit/typescript/card'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Link } from '../components/catalyst-ui-kit/typescript/link'
import { Text } from '../components/catalyst-ui-kit/typescript/text'

/* ---------------------------------------------------------------------------
   Production systems.

   These are closed-source systems built under commercial engagement. Two rules
   govern this data and must hold for anything added here:

   1. Disclosure - vendor names, partner identities and business financials are
      omitted. Every figure is either a personal contribution metric or a scale
      metric carrying no commercial detail.

   2. Attribution - describe only work authored here. Where a third party owns
      the behaviour (a reporting agency running a statutory notice sequence, an
      upstream service owning a rules engine), the copy says so and claims only
      the integration, orchestration or audit layer built around it. Anything
      stated here should survive an interviewer asking "walk me through how you
      implemented that".
   --------------------------------------------------------------------------- */
const PRODUCTION = [
  {
    number: '01',
    title: 'Age Verification & Compliance Platform',
    role: 'Sole architect and primary engineer',
    ownership: '90% of 433 commits',
    duration: '3.5 years, actively maintained',
    pitch:
      'Competitive youth sports depends on athletes being the age they claim. I built the operations platform that makes that enforceable: a compliance engine that evaluates every athlete registration in an event against a status-priority algorithm and surfaces exactly which records block certification.',
    challengeLabel: 'The Hard Part',
    challenge:
      'The age-verification rules lived inside a vendor-maintained service written in another language, which I did not control and could not change. I reimplemented that logic in Python and held it to behavioural parity - down to matching the original JSON serialisation byte-for-byte so records stayed interoperable across both systems. That let the tooling evolve on its own schedule without ever drifting from the source of truth.',
    highlights: [
      'Duplicate-registration detection across name and date-of-birth collisions, plus cross-roster conflict flagging',
      'Document-request workflows covering three distinct verification-failure modes with agent-editable templates',
      'Clean Architecture across 26 apps: framework-free domain layer, ports and adapters for every external system, domain events across bounded contexts',
    ],
    metrics: [
      { label: 'Django apps', value: '26' },
      { label: 'Tests', value: '413' },
      { label: 'Ownership', value: '90%' },
    ],
    tags: ['Django', 'Python', 'MySQL', 'DDD', 'Clean Architecture', 'GCP'],
    accent: 'cyan' as const,
  },
  {
    number: '02',
    title: 'Coach Credentialing & Background Check Platform',
    role: 'Architect and primary engineer',
    ownership: '93% of 571 commits',
    duration: 'Since 2024, actively maintained',
    pitch:
      'The Django platform that fronts a partner-facing sports ecosystem and handles coach credentialing end to end - registration, waivers, payment, background screening and roster provisioning - across multiple external partner integrations.',
    challengeLabel: 'Integrating a Regulated Vendor',
    challenge:
      "Background screening is carried out by a regulated reporting agency that owns the legally mandated notice and dispute sequence. My work was the boundary around it. An adverse action refuses to start if one is already in progress, delegates to the agency, then commits the local status change and an immutable audit record inside a single transaction - persisting the agency's raw response, because that is what actually defends a dispute months later. Agency failures surface as gateway errors instead of being masked as our own, and adverse-action history is protected from deletion even if its parent case is removed.",
    highlights: [
      'Multi-step registration state machine with independently timestamped dual waiver acceptance',
      'Idempotency-keyed payment capture, so a retried checkout request cannot double-charge',
      'Jurisdiction-aware fee calculation, expiring magic-link registration, and scoped credential bundles per external partner',
    ],
    metrics: [
      { label: 'Django apps', value: '13' },
      { label: 'Tests', value: '145' },
      { label: 'Ownership', value: '93%' },
    ],
    tags: ['Django', 'DRF', 'MySQL', 'Payments', 'State Machines', 'GCP'],
    accent: 'magenta' as const,
  },
  {
    number: '03',
    title: 'Multi-Tenant Recruiting CRM',
    role: 'Backend architect',
    ownership: '88% of 156 commits',
    duration: 'Serving 600+ tenant organizations',
    pitch:
      'A collaborative recruiting CRM built on configurable boards, columns and leads, with realtime updates streamed to every connected teammate. The backend serves a REST API and a WebSocket interface from a single ASGI deployment.',
    challengeLabel: 'Isolation Under Load',
    challenge:
      "Multi-tenancy is only as strong as its weakest query. Every list endpoint scopes to the caller's tenant through the ownership chain rather than trusting a request parameter, and every viewset falls back to an empty queryset by default - so a missing scope yields nothing instead of leaking another tenant's data. Schema generation runs against those same empty defaults and can never expose real records.",
    highlights: [
      'ASGI and Channels serving REST and WebSocket protocols from one deployment, with presence heartbeats for live collaborator tracking',
      'JWT authentication with refresh-token rotation and blacklisting on logout',
      'Asynchronous lead-import pipeline with progress streaming, plus separate activity, audit and login event trails',
    ],
    metrics: [
      { label: 'Tenants', value: '600+' },
      { label: 'Tests', value: '340' },
      { label: 'Ownership', value: '88%' },
    ],
    tags: ['Django', 'DRF', 'Channels', 'Redis', 'Django-Q', 'WebSockets'],
    accent: 'cyan' as const,
  },
  {
    number: '04',
    title: 'Competitive Rating & Entity Resolution',
    role: 'Sole implementer',
    ownership: '18 of 18 commits',
    duration: 'Scoring methodology developed with the business',
    pitch:
      'A proprietary rating system that ranks teams across events where no two competitors share a full schedule, propagating strength of schedule transitively through the opponent graph. I productionised it from a standalone analytical script into discrete domain services under Clean Architecture.',
    challengeLabel: 'The Harder Problem Was Identity',
    challenge:
      'Rankings key on team ID, but the same real-world club routinely appears as several records - registered under separate partner portals, or duplicated outright by coaches. Every duplicate splits a win/loss record in half and distorts strength of schedule for every opponent it touches. So I built the entity resolution layer around it: two teams that met in the same event are definitionally distinct no matter how far their rosters overlap, a shared-coaching-staff gate means athlete movement between clubs can never trigger a merge on its own, and tiered confidence routes the ambiguous middle to human review instead of guessing. Confirmed decisions persist as durable facts rather than one-off overrides.',
    highlights: [
      'Rating logic split into calculation, strength-of-schedule and assembly services, each testable without a database',
      'Roster-overlap detection computed in SQL across event rosters, scoped by partner and season',
      'Confirm, dismiss and manual-alias use cases, so human judgement is captured once and reused everywhere',
    ],
    metrics: [
      { label: 'Domain services', value: '3' },
      { label: 'Code authored', value: '100%' },
      { label: 'Running since', value: '2023' },
    ],
    tags: ['Python', 'Django', 'MySQL', 'Entity Resolution', 'DDD', 'Graph Traversal'],
    accent: 'magenta' as const,
  },
]

/* Open-source demos. Kept deliberately compact - the full architecture write-up
   for each lives on its own demo page, where a reader who clicked through
   actually wants it. */
const DEMOS = [
  {
    number: '01',
    title: 'Secure Client Portal',
    pitch:
      'Client organizations manage projects, files, deliverables, invoices and approvals behind per-organization isolation.',
    architectureLine:
      'A framework-free domain layer of 12 entities and 20 use cases, with an explicit approval state machine keeping business rules out of the views.',
    tags: ['Django', 'DRF', 'React', 'GCS'],
    demoPath: '/portal',
    accent: 'cyan' as const,
  },
  {
    number: '02',
    title: 'Operations Dashboard',
    pitch:
      'KPIs, time-series charts, filters and threshold alerts over raw business data.',
    architectureLine:
      'Alert evaluation runs on a scheduled worker rather than in the request cycle, and exports stream as CSV so large datasets never buffer in memory.',
    tags: ['Django', 'DRF', 'React', 'Recharts'],
    demoPath: '/dashboard',
    accent: 'magenta' as const,
  },
  {
    number: '03',
    title: 'Workflow Automation Engine',
    pitch:
      'Users compose triggers, conditions and actions into rules - an internal Zapier for business workflows.',
    architectureLine:
      'A decorator-based registry adds new triggers and actions without touching the engine, and dry-run mode evaluates every condition while dispatching nothing.',
    tags: ['Django', 'DRF', 'React', 'Twilio'],
    demoPath: '/automations',
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

function useReveal(refs: React.RefObject<HTMLElement | null>[]) {
  useEffect(() => {
    const containers = refs.map((r) => r.current).filter(Boolean) as HTMLElement[]
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}

export default function ProjectsPage() {
  const productionRef = useRef<HTMLDivElement>(null)
  const cardsRef = useRef<HTMLDivElement>(null)
  const ecosystemRef = useRef<HTMLDivElement>(null)

  useReveal([productionRef, cardsRef, ecosystemRef])

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
          Production Systems &amp; Architecture
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
          Four production platforms I architected and continue to maintain - regulated
          compliance workflows, payment processing, multi-tenant realtime systems and a
          competitive rating engine - followed by three open-source applications built to
          show the architecture behind them.
        </Text>
      </section>

      {/* ------------------------------------------------------------------
          Production work
          ------------------------------------------------------------------ */}
      <section className="relative pt-6 pb-16 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(255,0,255,0.05) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Shipped &amp; Running
            </Text>
            <Heading
              level={2}
              className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase"
            >
              Production Work
            </Heading>
            <Text className="text-sm max-w-2xl mx-auto mt-4 leading-relaxed">
              Systems serving real users under commercial engagement. Source is closed and
              client, vendor and partner identities are withheld - the architecture and my
              contribution are described in full.
            </Text>
          </div>

          <div className="flex flex-col gap-8" ref={productionRef}>
            {PRODUCTION.map((project, i) => (
              <Card
                key={project.title}
                flush
                accent={project.accent}
                data-delay={i * 100}
                className="reveal"
              >
                {/* Top bar */}
                <div className="flex items-center justify-between px-6 pt-6 pb-0">
                  <span className="font-display text-3xl font-bold text-cyber-border select-none">
                    {project.number}
                  </span>
                  <div className="flex items-center gap-3">
                    <Badge
                      color="emerald"
                      className="font-display text-[10px] tracking-widest uppercase"
                    >
                      In Production
                    </Badge>
                    <span className="text-[10px] font-display tracking-widest uppercase text-text-muted/60">
                      Private Source
                    </span>
                  </div>
                </div>

                <CardHeader>
                  <CardTitle className="text-neon-cyan text-base">{project.title}</CardTitle>
                  <Text className="text-[11px] font-display tracking-widest uppercase text-text-muted/70 mt-2">
                    {project.role} &middot; {project.ownership} &middot; {project.duration}
                  </Text>
                </CardHeader>

                <CardBody>
                  <Text className="text-sm leading-relaxed">{project.pitch}</Text>

                  {/* The engineering challenge */}
                  <div className="mt-4 border-l-2 border-neon-magenta/40 pl-4">
                    <Text className="text-[10px] font-display tracking-widest uppercase text-neon-magenta/60 mb-1">
                      {project.challengeLabel}
                    </Text>
                    <Text className="text-sm leading-relaxed">{project.challenge}</Text>
                  </div>

                  {/* Supporting detail */}
                  <div className="mt-4 border-l-2 border-neon-cyan/40 pl-4">
                    <Text className="text-[10px] font-display tracking-widest uppercase text-neon-cyan/60 mb-2">
                      Also Built
                    </Text>
                    <ul className="space-y-1">
                      {project.highlights.map((item, j) => (
                        <li key={j} className="flex gap-2 text-sm text-text-muted">
                          <span className="text-neon-cyan/40 select-none shrink-0 mt-0.5">
                            &#8250;
                          </span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Metrics strip */}
                  <div className="mt-5 grid grid-cols-3 gap-3">
                    {project.metrics.map((m) => (
                      <div
                        key={m.label}
                        className="bg-cyber-elevated border border-cyber-border rounded-lg px-1.5 sm:px-3 py-3 text-center"
                      >
                        <p className="font-display text-lg sm:text-xl font-bold text-neon-cyan">
                          {m.value}
                        </p>
                        <p className="text-[9px] sm:text-[10px] font-display tracking-wide sm:tracking-widest uppercase text-text-muted mt-1 leading-tight text-balance">
                          {m.label}
                        </p>
                      </div>
                    ))}
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
        </div>
      </section>

      {/* ------------------------------------------------------------------
          Open-source demonstrations
          ------------------------------------------------------------------ */}
      <section className="relative pt-8 pb-16 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 50% 50%, rgba(0,255,255,0.04) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Open Source &amp; Live
            </Text>
            <Heading
              level={2}
              className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase"
            >
              Architecture Demonstrations
            </Heading>
            <Text className="text-sm max-w-2xl mx-auto mt-4 leading-relaxed">
              The production systems above are closed source, so I built these three to make
              the same patterns inspectable - every line readable, every demo runnable in the
              browser.
            </Text>
            <div className="flex items-center justify-center gap-3 mt-6">
              <span className="w-2 h-2 rounded-full bg-neon-cyan" />
              <span className="text-neon-cyan text-xs font-display tracking-widest uppercase">
                All Three Live
              </span>
            </div>
          </div>

          <div className="grid gap-5 md:grid-cols-3" ref={cardsRef}>
            {DEMOS.map((project, i) => (
              <Card
                key={project.title}
                flush
                accent={project.accent}
                data-delay={i * 100}
                className="reveal flex flex-col h-full"
              >
                <div className="flex items-center justify-between px-5 pt-5">
                  <span className="font-display text-2xl font-bold text-cyber-border select-none">
                    {project.number}
                  </span>
                  <Badge
                    color="green"
                    className="font-display text-[10px] tracking-widest uppercase"
                  >
                    Live
                  </Badge>
                </div>

                <div className="px-5 pt-3 pb-5 flex flex-col grow">
                  <CardTitle className="text-neon-cyan text-sm leading-snug">
                    {project.title}
                  </CardTitle>

                  <Text className="text-sm leading-relaxed mt-2">{project.pitch}</Text>

                  <div className="mt-3 border-l-2 border-neon-cyan/40 pl-3">
                    <Text className="text-xs leading-relaxed text-text-muted">
                      {project.architectureLine}
                    </Text>
                  </div>

                  {/* mt-auto pins the demo link to the card floor so all three
                      align, regardless of how much copy sits above it. */}
                  <div className="flex flex-wrap gap-1.5 mt-4 mb-4">
                    {project.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 text-[10px] font-display tracking-wide text-text-muted border border-cyber-border rounded uppercase"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <Link
                    href={project.demoPath}
                    className="mt-auto pt-3 border-t border-cyber-border text-xs font-display tracking-widest uppercase text-neon-cyan hover:glow-cyan transition-all"
                  >
                    Try Demo &rarr;
                  </Link>
                </div>
              </Card>
            ))}
          </div>
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
            <Heading
              level={2}
              className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase"
            >
              The Ecosystem
            </Heading>
            <Text className="text-sm max-w-2xl mx-auto mt-4 leading-relaxed">
              The three demonstrations are not isolated apps - they share a common automation
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
                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-4 text-center">
                  <Text className="text-[10px] font-display tracking-widest uppercase mb-1">
                    Source
                  </Text>
                  <Text className="font-display text-sm font-bold text-text-primary">
                    {step.from}
                  </Text>
                </div>

                <div className="flex flex-col items-center gap-2">
                  <span className="text-[10px] font-mono text-neon-cyan/70 tracking-wide">
                    {step.event}
                  </span>
                  <div className="flex items-center gap-3 w-full">
                    <span className="text-neon-cyan select-none">&#8594;</span>
                    <div className="flex-1 bg-cyber-elevated border border-neon-cyan/30 rounded-xl px-3 py-3 text-center">
                      <p className="font-display text-xs font-bold text-neon-cyan">
                        Automation Engine
                      </p>
                    </div>
                    <span className="text-neon-magenta select-none">&#8594;</span>
                  </div>
                </div>

                <div className="bg-cyber-elevated border border-cyber-border rounded-xl px-5 py-4 text-center">
                  <Text className="text-[10px] font-display tracking-widest uppercase mb-1">
                    Result
                  </Text>
                  <Text className="font-display text-sm font-bold text-neon-green">
                    {step.result}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
