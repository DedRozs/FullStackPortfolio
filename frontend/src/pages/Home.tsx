import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import SEO, { JsonLd, generateWebsiteSchema, generatePersonSchema, generateProfessionalServiceSchema } from '../components/SEO'

interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  tags: string[]
  published_at: string
  read_time: number
}

const roles = [
  'CTO & Technical Leader',
  'Full Stack Engineer',
  'API Architect',
  'Team Builder',
]

const techStack = [
  { name: 'Python', icon: '🐍' },
  { name: 'TypeScript', icon: '📘' },
  { name: 'React', icon: '⚛️' },
  { name: 'Django', icon: '🎸' },
  { name: 'PostgreSQL', icon: '🐘' },
  { name: 'Redis', icon: '🔴' },
  { name: 'AWS', icon: '☁️' },
  { name: 'Docker', icon: '🐳' },
  { name: 'Kubernetes', icon: '☸️' },
  { name: 'GitHub Actions', icon: '🔄' },
]

const highlights = [
  {
    title: 'Sports Thread',
    role: 'CTO',
    description: 'Leading engineering for a sports apparel platform serving over half a million users. Built the entire tech stack from zero to production.',
    metrics: ['2M+ Users', 'REST API', 'React Native'],
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    title: 'Scalable Systems',
    role: 'Architect',
    description: 'Designing and implementing clean architecture patterns that scale with business growth.',
    metrics: ['DDD', 'Clean Architecture', 'Event-Driven'],
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    title: 'Team Leadership',
    role: 'Mentor',
    description: 'Building and mentoring engineering teams. Creating cultures of excellence and continuous learning.',
    metrics: ['Code Reviews', 'Best Practices', 'Growth'],
    gradient: 'from-orange-500 to-red-500',
  },
]

export default function Home() {
  const [recentPosts, setRecentPosts] = useState<BlogPost[]>([])
  const [loading, setLoading] = useState(true)
  const [currentRoleIndex, setCurrentRoleIndex] = useState(0)
  const [displayedText, setDisplayedText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  // Typing effect
  useEffect(() => {
    const currentRole = roles[currentRoleIndex]
    const typingSpeed = isDeleting ? 50 : 100
    const pauseTime = isDeleting ? 500 : 2000

    if (!isDeleting && displayedText === currentRole) {
      setTimeout(() => setIsDeleting(true), pauseTime)
      return
    }

    if (isDeleting && displayedText === '') {
      setIsDeleting(false)
      setCurrentRoleIndex((prev) => (prev + 1) % roles.length)
      return
    }

    const timeout = setTimeout(() => {
      setDisplayedText((prev) =>
        isDeleting
          ? prev.slice(0, -1)
          : currentRole.slice(0, prev.length + 1)
      )
    }, typingSpeed)

    return () => clearTimeout(timeout)
  }, [displayedText, isDeleting, currentRoleIndex])

  useEffect(() => {
    const fetchRecentPosts = async () => {
      try {
        const response = await fetch('/api/blog/posts/?page_size=3')
        if (response.ok) {
          const data = await response.json()
          setRecentPosts(data.posts)
        }
      } catch (error) {
        console.error('Error fetching recent posts:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRecentPosts()
  }, [])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <>
      <SEO
        title="Home"
        description="Joseph Prince - CTO at Sports Thread and Full Stack Software Engineer. Building scalable sports event management systems with Python, TypeScript, React, and Django. Not the pastor - a tech professional serving 2M+ users."
        tags={['Joseph Prince CTO', 'Joseph Prince Software Engineer', 'Joseph Prince Developer', 'Sports Thread', 'Full Stack Engineer', 'Python Developer', 'React Developer', 'Django Developer']}
      />
      <JsonLd data={generateWebsiteSchema()} />
      <JsonLd data={generatePersonSchema()} />
      <JsonLd data={generateProfessionalServiceSchema()} />

      {/* Hero Section */}
      <section className="min-h-[90vh] flex items-center relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="max-w-4xl">
            {/* Status badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-dark-800/80 border border-gray-700 rounded-full mb-8 backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-sm text-gray-300">Available for consulting</span>
            </div>

            <p className="text-blue-400 font-medium mb-4 text-lg">Hi, I'm</p>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                Joseph Prince
              </span>
            </h1>
            
            {/* Typing effect */}
            <div className="h-12 mb-8">
              {/* Screen reader accessible version */}
              <span className="sr-only" aria-live="polite">
                {roles[currentRoleIndex]}
              </span>
              <p className="text-2xl md:text-3xl text-gray-300" aria-hidden="true">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  {displayedText}
                </span>
                <span className="animate-pulse text-blue-400">|</span>
              </p>
            </div>

            <p className="text-lg md:text-xl text-gray-400 mb-10 leading-relaxed max-w-2xl">
              Building{' '}
              <span className="text-white font-medium">scalable systems</span> and leading{' '}
              <span className="text-white font-medium">engineering teams</span> at Sports Thread. 
              I turn complex problems into elegant, maintainable solutions.
            </p>

            <div className="flex flex-wrap gap-4 mb-12">
              <Link
                to="/blog"
                className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
              >
                <span className="flex items-center gap-2">
                  Read the Blog
                  <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </Link>
              <Link
                to="/contact"
                className="px-8 py-4 border border-gray-600 hover:border-blue-500 hover:bg-blue-500/10 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5"
              >
                Get in Touch
              </Link>
              <a
                href="https://github.com/DedRozs"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-4 bg-dark-800 hover:bg-dark-700 border border-gray-700 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
              </a>
            </div>

            {/* Quick stats */}
            <div className="flex flex-wrap gap-8 pt-8 border-t border-gray-800">
              <div>
                <p className="text-3xl font-bold text-white">4+</p>
                <p className="text-gray-500 text-sm">Years Experience</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-white">10+</p>
                <p className="text-gray-500 text-sm">Projects Shipped</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-white">2M+</p>
                <p className="text-gray-500 text-sm">Users Impacted</p>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="py-16 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-gray-500 mb-8 text-sm uppercase tracking-wider">Technologies I Work With</p>
          <div className="flex flex-wrap justify-center gap-4">
            {techStack.map((tech) => (
              <div
                key={tech.name}
                className="group px-5 py-3 bg-dark-800/50 hover:bg-dark-700 border border-gray-800 hover:border-gray-600 rounded-xl transition-all duration-300 cursor-default hover:-translate-y-1"
              >
                <span className="flex items-center gap-2">
                  <span className="text-xl">{tech.icon}</span>
                  <span className="text-gray-300 group-hover:text-white transition-colors">{tech.name}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Highlights Section */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              What I Do
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              From startup MVPs to enterprise systems, I bring ideas to life with clean code and pragmatic architecture.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {highlights.map((item, index) => (
              <div
                key={item.title}
                className="group relative p-6 bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl transition-all duration-500 hover:-translate-y-2"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Gradient accent */}
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${item.gradient} rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />
                
                <div className="mb-4">
                  <span className={`text-xs font-medium px-3 py-1 rounded-full bg-gradient-to-r ${item.gradient} text-white`}>
                    {item.role}
                  </span>
                </div>
                
                <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300 transition-all">
                  {item.title}
                </h3>
                
                <p className="text-gray-400 mb-6 text-sm leading-relaxed">
                  {item.description}
                </p>
                
                <div className="flex flex-wrap gap-2">
                  {item.metrics.map((metric) => (
                    <span
                      key={metric}
                      className="px-2 py-1 bg-dark-700 text-gray-400 text-xs rounded-md"
                    >
                      {metric}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Posts Section */}
      <section className="py-20 bg-dark-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-end mb-10">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Recent Posts
              </h2>
              <p className="text-gray-400">
                Thoughts on engineering, leadership, and building things.
              </p>
            </div>
            <Link
              to="/blog"
              className="text-blue-400 hover:text-blue-300 font-medium transition"
            >
              View all →
            </Link>
          </div>

          {loading ? (
            <div className="grid gap-6 md:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-dark-800 rounded-xl p-6 animate-pulse">
                  <div className="h-6 bg-dark-700 rounded w-3/4 mb-4"></div>
                  <div className="h-4 bg-dark-700 rounded w-full mb-2"></div>
                  <div className="h-4 bg-dark-700 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ) : recentPosts.length === 0 ? (
            <div className="text-center py-12 bg-dark-800 rounded-xl">
              <p className="text-gray-400">
                No posts yet. Check back soon!
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-3">
              {recentPosts.map((post) => (
                <article
                  key={post.id}
                  className="group relative bg-dark-800 hover:bg-dark-700/80 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1"
                >
                  <Link to={`/blog/${post.slug}`}>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {post.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs font-medium rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-3 group-hover:text-blue-400 transition-colors line-clamp-2">
                      {post.title}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4 line-clamp-2 leading-relaxed">
                      {post.excerpt}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <time dateTime={post.published_at}>
                        {formatDate(post.published_at)}
                      </time>
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        {post.read_time} min
                      </span>
                    </div>
                  </Link>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="relative p-10 md:p-16 bg-gradient-to-br from-blue-600/20 via-dark-800 to-purple-600/20 border border-gray-700 rounded-3xl text-center overflow-hidden">
            {/* Background decoration */}
            <div className="absolute top-0 left-1/4 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl" />
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Let's Build Something Great
              </h2>
              <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                Whether you need technical leadership, a new product built, or just want to chat about architecture—I'm always open to interesting conversations.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="px-8 py-4 bg-white text-dark-900 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-300 hover:-translate-y-0.5 shadow-xl"
                >
                  Start a Conversation
                </Link>
                <Link
                  to="/about"
                  className="px-8 py-4 border border-gray-600 text-white font-medium rounded-xl hover:border-white transition-all duration-300 hover:-translate-y-0.5"
                >
                  Learn More About Me
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
