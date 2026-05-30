import { useEffect, useRef } from 'react'
import { Badge } from '../components/catalyst-ui-kit/typescript/badge'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Card, CardHeader, CardBody, CardFooter, CardTitle, CardDescription } from '../components/catalyst-ui-kit/typescript/card'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../components/catalyst-ui-kit/typescript/text'
import heroVideo from '../assets/11041434-hd_1920_1080_30fps.mp4'

const HERO_VIDEO_SRC = heroVideo

const PROJECTS_IN_DEVELOPMENT = [
  {
    title: 'Secure Client Portal',
    pitch: 'Full-stack portal for managing projects, files, deliverables, invoices, and approvals across multiple client organizations.',
    tags: ['Django', 'DRF', 'React', 'GCS', 'SendGrid'],
  },
  {
    title: 'Operations Dashboard',
    pitch: 'Internal analytics dashboard with KPI cards, time-series charts, alert rules, and scheduled metric evaluation.',
    tags: ['Django', 'DRF', 'React', 'Recharts', 'Django-Q2'],
  },
  {
    title: 'Workflow Automation Engine',
    pitch: 'Trigger-condition-action rule builder that connects the portal and dashboard into an event-driven automation ecosystem.',
    tags: ['Django', 'DRF', 'React', 'Twilio', 'SendGrid'],
  },
]

const EXPERTISE = [
  {
    area: 'Backend & Architecture',
    description:
      'Production Django systems built for scale. Clean Architecture, domain-driven design, REST APIs, and the discipline to keep them maintainable years later.',
    tags: ['Python', 'Django', 'REST APIs', 'Clean Architecture'],
  },
  {
    area: 'Full-Stack Delivery',
    description:
      'End-to-end feature delivery from database schema to React component. CI/CD pipelines, Docker, and shipping without breaking things.',
    tags: ['React', 'TypeScript', 'Docker', 'PostgreSQL', 'GitHub Actions'],
  },
  {
    area: 'Cloud & AI Integration',
    description:
      'Cloud deployments across GCP and AWS - App Engine, Cloud Run, EC2, RDS. OpenAI API integration with production-grade reliability.',
    tags: ['GCP', 'AWS', 'MySQL', 'PostgreSQL', 'OpenAI'],
  },
]

export default function HomePage() {
  const cardsRef = useRef<HTMLDivElement>(null)
  const projectsCardsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const containers = [cardsRef.current, projectsCardsRef.current].filter(Boolean) as HTMLDivElement[]
    if (containers.length === 0) return

    const cards = containers.flatMap(c => Array.from(c.querySelectorAll<HTMLElement>('.reveal')))
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
      { threshold: 0.1 },
    )
    cards.forEach((card) => observer.observe(card))
    return () => observer.disconnect()
  }, [])
  return (
    <>
      <section className="scanlines relative min-h-[80dvh] flex flex-col items-center justify-center text-center px-6 py-24 overflow-hidden">
        {/* Background video loop */}
        {HERO_VIDEO_SRC && (
          <video
            className="absolute inset-0 w-full h-full object-cover -z-10 motion-safe:block hidden"
            src={HERO_VIDEO_SRC}
            autoPlay
            loop
            muted
            playsInline
            aria-hidden="true"
          />
        )}
        {/* Dark overlay - keeps text readable over the video */}
        {HERO_VIDEO_SRC && (
          <div className="absolute inset-0 -z-10 bg-cyber-dark/70" aria-hidden="true" />
        )}
        {/* Hero text card - frosted backdrop for legibility over video */}
        <div className="relative flex flex-col items-center text-center px-8 py-10 rounded-2xl bg-cyber-dark/60 border border-cyber-border/50 backdrop-blur-sm max-w-3xl w-full">
          {/* Availability badge */}
          <div
            className="flex items-center gap-2 px-4 py-1.5 border border-neon-green text-neon-green text-xs font-display tracking-widest uppercase mb-8 animate-fade-in-up"
            style={{ animationDelay: '0s' }}
          >
            <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            Available for New Projects
          </div>

          <Text
            className="text-neon-magenta text-sm font-display tracking-[0.4em] uppercase mb-4 animate-fade-in-up"
            style={{ animationDelay: '0.1s' }}
          >
            Full Stack Developer &amp; Consultant
          </Text>

          <Heading
            level={1}
            className="font-display text-5xl sm:text-7xl font-bold tracking-tight text-text-primary mb-2 animate-fade-in-up"
            style={{ animationDelay: '0.2s' }}
          >
            Joseph{' '}
            <span className="text-neon-cyan glow-cyan animate-glitch">Prince</span>
          </Heading>

          <Text
            className="text-lg max-w-2xl mt-6 leading-relaxed animate-fade-in-up"
            style={{ animationDelay: '0.3s' }}
          >
            I build and scale production SaaS platforms. Four years at Sports Thread - from
            Marketing Manager to CTO - owning architecture, shipping features, and keeping
            systems reliable at scale.
            <br /><br />
            <span className="text-neon-cyan">Available for senior roles and consulting engagements.</span>
          </Text>

          <div
            className="flex flex-wrap gap-4 mt-10 justify-center animate-fade-in-up"
            style={{ animationDelay: '0.4s' }}
          >
            <Button color="neon-cyan" href="/projects" className="font-display tracking-widest uppercase">
              View Projects
            </Button>
            <Button color="neon-magenta-outline" href="/ai" className="font-display tracking-widest uppercase">
              AI Assistant
            </Button>
            <Button color="neon-cyan-outline" href="/contact" className="font-display tracking-widest uppercase">
              Get In Touch
            </Button>
          </div>
        </div>
      </section>

      {/* Expertise pillars */}
      <section className="relative overflow-hidden py-24">
        {/* Radial glow behind the cards */}
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(59,27,114,0.35) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          {/* Section heading */}
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              Core Expertise
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              What I Do
            </Heading>
          </div>

          <div className="grid sm:grid-cols-3 gap-6" ref={cardsRef}>
            {EXPERTISE.map((pillar, i) => (
              <Card
                key={pillar.area}
                flush
                data-delay={i * 120}
                className="reveal cursor-default"
              >
                <CardHeader className="items-center text-center">
                  <CardTitle className="text-neon-cyan">{pillar.area}</CardTitle>
                </CardHeader>
                <CardBody className="items-center text-center">
                  <CardDescription>{pillar.description}</CardDescription>
                </CardBody>
                <CardFooter className="sm:min-h-[148px]">
                  {pillar.tags.map((tag) => (
                    <span
                      key={tag}
                      className="flex-1 basis-[calc(50%-4px)] px-2 py-1.5 text-xs font-display tracking-wide text-text-muted border border-cyber-border rounded uppercase text-center whitespace-nowrap"
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
      {/* Projects in development */}
      <section className="relative overflow-hidden py-24">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,255,255,0.06) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Text className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3">
              In Development
            </Text>
            <Heading level={2} className="font-display text-2xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase">
              What I&apos;m Building
            </Heading>
          </div>

          <div className="grid sm:grid-cols-3 gap-6" ref={projectsCardsRef}>
            {PROJECTS_IN_DEVELOPMENT.map((project, i) => (
              <Card key={project.title} flush data-delay={i * 120} className="reveal cursor-default">
                <CardHeader className="items-center text-center">
                  <Badge color="neon-magenta" className="mb-2 font-display text-[10px] tracking-widest uppercase self-center">
                    In Development
                  </Badge>
                  <CardTitle className="text-text-primary">{project.title}</CardTitle>
                </CardHeader>
                <CardBody className="items-center text-center">
                  <CardDescription>{project.pitch}</CardDescription>
                </CardBody>
                <CardFooter>
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="flex-1 basis-[calc(50%-4px)] px-2 py-1.5 text-xs font-display tracking-wide text-text-muted border border-cyber-border rounded uppercase text-center whitespace-nowrap"
                    >
                      {tag}
                    </span>
                  ))}
                </CardFooter>
              </Card>
            ))}
          </div>

          <div className="text-center mt-10">
            <Button color="neon-cyan-outline" href="/projects" className="font-display tracking-widest uppercase">
              View Projects Page
            </Button>
          </div>
        </div>
      </section>
    </>
  )
}
