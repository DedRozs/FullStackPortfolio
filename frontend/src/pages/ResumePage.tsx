import { SKILL_GROUPS } from '../data/skills'

/* A résumé, not a second About page - bullets carry outcomes, not duties.
   Same disclosure rules as the rest of the site: no vendor, partner or client
   names, no commercial figures. Contribution percentages come from git history.

   This renders in the site theme on screen and as a plain document in print,
   so "Download PDF" is just the browser's own print-to-PDF. That keeps one
   source of truth - there is no separate PDF to drift out of date. */

const CONTACT = [
  { label: 'thejosephprince.com', href: 'https://www.thejosephprince.com' },
  { label: 'linkedin.com/in/thejprince', href: 'https://linkedin.com/in/thejprince' },
  { label: 'github.com/dedrozs', href: 'https://github.com/dedrozs' },
]

const EXPERIENCE = [
  {
    title: 'Chief Technology Officer',
    org: 'Sports Thread',
    period: 'Jan 2026 – Present',
    bullets: [
      'Own architecture, scalability and security across the platform, and set technical direction for all engineering work.',
      'Provide engineering oversight of the outsourced vendor team maintaining the core platform: audited their codebase and produced a cost-engineering assessment that sized each remediation and reclassified a misdiagnosed infrastructure issue.',
      'Authored a technical proposal analysing four independent authentication systems across roughly 350 routes; accepted and implemented.',
      'Remain the highest-output individual contributor on the team - authored commit volume has increased every year since 2022, with 2026 the highest to date.',
    ],
  },
  {
    title: 'VP of Software Development',
    org: 'Sports Thread',
    period: 'Nov 2023 – Jan 2026',
    bullets: [
      'Architected and wrote the Django platform fronting partner integrations and coach credentialing end to end - registration, waivers, payment, third-party screening and roster provisioning (93% of 571 commits).',
      'Built the multi-tenant recruiting CRM backend serving 600+ tenant organizations: REST and WebSocket from a single ASGI deployment, JWT with refresh-token rotation and blacklisting, async import pipeline with progress streaming (88% of 156 commits, 340 tests).',
      'Hired and manage the frontend developer building against these APIs.',
    ],
  },
  {
    title: 'Director of Software Engineering',
    org: 'Sports Thread',
    period: 'Jun 2022 – Nov 2023',
    bullets: [
      'Built the age-verification and compliance platform that remains the operational backbone of event certification - 26 Django apps, 413 tests, 90% of 433 commits sustained over 3.5 years.',
      'Reimplemented business rules from a vendor-maintained service written in another language and held them to behavioural parity, down to byte-identical JSON serialisation so records stayed interoperable across both systems.',
      'Established the Clean Architecture and domain-driven design standard that every subsequent backend was built on.',
    ],
  },
  {
    title: 'Marketing Manager',
    org: 'Sports Thread',
    period: 'Jan 2022 – Jun 2022',
    bullets: [
      'Hired into a non-technical role and began writing production code against real company problems within weeks; the engineering title followed six months later.',
    ],
  },
]

const SYSTEMS = [
  {
    name: 'Age Verification & Compliance Platform',
    scope: 'Sole architect · 90% of 433 commits · 3.5 years',
    summary:
      'Compliance engine evaluating every athlete registration in an event against a status-priority algorithm to surface exactly what blocks certification. Duplicate-registration detection across name/DOB collisions, cross-roster conflict flagging, and document-request workflows across three verification-failure modes.',
    stack: 'Django · MySQL · Clean Architecture · DDD · GCP',
  },
  {
    name: 'Coach Credentialing & Background Check Platform',
    scope: 'Architect · 93% of 571 commits · active',
    summary:
      'Onboarding end to end across multiple external partner integrations. Screening is performed by a regulated third-party agency; built the boundary around it - duplicate adverse actions refused, local state and an immutable audit record committed in a single transaction, agency failures surfaced as gateway errors rather than masked.',
    stack: 'Django · DRF · MySQL · Payments · State machines',
  },
  {
    name: 'Multi-Tenant Recruiting CRM (backend)',
    scope: 'Backend architect · 88% of 156 commits · 600+ tenants',
    summary:
      'Collaborative boards with realtime updates streamed to every connected teammate. Tenant isolation enforced at the query layer: every endpoint scopes through the ownership chain rather than trusting a request parameter, and every viewset defaults to an empty queryset so a missing scope leaks nothing.',
    stack: 'Django · Channels · Redis · ASGI · WebSockets',
  },
  {
    name: 'Competitive Rating & Entity Resolution',
    scope: 'Sole implementer · methodology developed with the business',
    summary:
      'Rating system for teams that never share a full schedule, propagating strength of schedule transitively through the opponent graph. Built the entity resolution layer that stops one real-world club counting as several - a shared-staff gate prevents false merges, and tiered confidence routes ambiguous pairs to human review rather than guessing.',
    stack: 'Python · Django · MySQL · Graph traversal',
  },
]

const CREDENTIALS = [
  'B.S. Computer Science — Colorado Technical University (2026)',
  'Certified Scrum Master, Product Owner & Developer (CSM, CSPO, CSD) — Scrum Alliance',
  'Digital Marketing Immersion — Thinkful',
]

function Rule() {
  return (
    <div className="h-px bg-cyber-border print:bg-neutral-300 my-4 print:my-3" />
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-display text-xs tracking-[0.3em] uppercase text-neon-cyan print:text-black print:font-bold mb-3">
      {children}
    </h2>
  )
}

export default function ResumePage() {
  return (
    <div className="resume-root max-w-3xl mx-auto px-6 py-12 print:px-0 print:py-0 print:max-w-none">
      {/* Screen-only action bar */}
      <div className="no-print flex flex-wrap items-center justify-between gap-4 mb-8">
        <p className="text-sm text-text-muted">
          Use your browser&apos;s print dialog and choose &ldquo;Save as PDF&rdquo;.
        </p>
        <a
          href="/resume/pdf/"
          download
          className="px-5 py-2.5 text-xs font-display tracking-widest uppercase text-neon-cyan border border-neon-cyan/50 rounded hover:border-neon-cyan hover:glow-cyan transition-all"
        >
          Download PDF &darr;
        </a>
      </div>

      <article className="text-text-primary print:text-black">
        {/* Header */}
        <header>
          <h1 className="font-display text-3xl print:text-2xl font-bold tracking-wide text-neon-cyan print:text-black">
            Joseph Prince
          </h1>
          <p className="font-display text-xs tracking-[0.25em] uppercase text-neon-magenta print:text-neutral-700 mt-2">
            CTO · Staff-Level Backend Engineer
          </p>
          <p className="text-sm text-text-muted print:text-neutral-700 mt-3">
            Remote (US) · Denver, Colorado (MT) ·{' '}
            {CONTACT.map((c, i) => (
              <span key={c.href}>
                {i > 0 && ' · '}
                <a href={c.href} className="text-neon-cyan print:text-black hover:underline">
                  {c.label}
                </a>
              </span>
            ))}
          </p>
        </header>

        <Rule />

        {/* Summary */}
        <section>
          <SectionHeading>Summary</SectionHeading>
          <p className="text-sm leading-relaxed text-text-muted print:text-black">
            Engineering leader who never stopped shipping. Primary author of four production
            backend systems - regulated compliance workflows, payment and screening pipelines,
            multi-tenant realtime services - built and maintained over four years at the same
            company while progressing from a non-technical marketing role to CTO, fully remote
            the entire time. Manages a developer, directs an outsourced vendor team, and still
            writes and reviews production code every week.
          </p>
        </section>

        <Rule />

        {/* Experience */}
        <section>
          <SectionHeading>Experience</SectionHeading>
          <div className="space-y-5">
            {EXPERIENCE.map((role) => (
              <div key={role.title} className="break-inside-avoid">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                  <h3 className="font-display text-sm font-bold tracking-wide text-text-primary print:text-black">
                    {role.title}
                    <span className="text-text-muted print:text-neutral-700 font-normal">
                      {' '}· {role.org}
                    </span>
                  </h3>
                  <span className="text-xs font-display tracking-wide text-text-muted print:text-neutral-700">
                    {role.period}
                  </span>
                </div>
                <ul className="mt-2 space-y-1.5">
                  {role.bullets.map((b, i) => (
                    <li
                      key={i}
                      className="flex gap-2 text-sm leading-relaxed text-text-muted print:text-black"
                    >
                      <span className="text-neon-cyan/50 print:text-black shrink-0">&#8226;</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <Rule />

        {/* Selected systems */}
        <section className="break-before-page print:break-before-page">
          <SectionHeading>Selected Production Systems</SectionHeading>
          <p className="text-xs text-text-muted print:text-neutral-700 mb-4 italic">
            Closed source. Client, vendor and partner identities withheld; architecture and
            personal contribution described in full.
          </p>
          <div className="space-y-4">
            {SYSTEMS.map((s) => (
              <div key={s.name} className="break-inside-avoid">
                <h3 className="font-display text-sm font-bold tracking-wide text-text-primary print:text-black">
                  {s.name}
                </h3>
                <p className="text-xs font-display tracking-wide text-neon-cyan/70 print:text-neutral-700 mt-0.5">
                  {s.scope}
                </p>
                <p className="text-sm leading-relaxed text-text-muted print:text-black mt-1.5">
                  {s.summary}
                </p>
                <p className="text-xs text-text-muted/80 print:text-neutral-700 mt-1">
                  {s.stack}
                </p>
              </div>
            ))}
          </div>
        </section>

        <Rule />

        {/* Skills */}
        <section className="break-inside-avoid">
          <SectionHeading>Skills</SectionHeading>
          <dl className="space-y-1.5">
            {SKILL_GROUPS.map((group) => (
              <div key={group.area} className="flex flex-wrap gap-x-2 text-sm">
                <dt className="font-display text-xs tracking-wide uppercase text-neon-cyan/70 print:text-black print:font-bold w-40 shrink-0">
                  {group.area}
                </dt>
                <dd className="text-text-muted print:text-black flex-1 min-w-0">
                  {group.skills.join(' · ')}
                </dd>
              </div>
            ))}
          </dl>
        </section>

        <Rule />

        {/* Education */}
        <section className="break-inside-avoid">
          <SectionHeading>Education &amp; Certifications</SectionHeading>
          <ul className="space-y-1">
            {CREDENTIALS.map((c) => (
              <li key={c} className="text-sm text-text-muted print:text-black">
                {c}
              </li>
            ))}
          </ul>
        </section>
      </article>
    </div>
  )
}
