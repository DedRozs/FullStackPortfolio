import { Link } from 'react-router-dom'
import SEO, { JsonLd, generatePersonSchema, generateBreadcrumbSchema, generateFAQSchema, generateProfilePageSchema } from '../components/SEO'

const experience = [
  {
    role: 'Chief Technology Officer',
    company: 'Sports Thread',
    period: 'Jan 2026 — Present',
    description: 'Hands-on technical leader responsible for building and scaling the platform. Actively contributing code while setting technical direction and engineering best practices.',
    highlights: ['Platform architecture', 'Production code & reviews', 'Technical strategy'],
    current: true,
  },
  {
    role: 'VP of Software Development',
    company: 'Sports Thread',
    period: 'Nov 2023 — Jan 2026',
    description: 'Provided strategic direction and technical leadership. Designed scalable, secure architectures and evaluated technologies to enhance development efficiency.',
    highlights: ['Technical leadership', 'Architecture design', 'Internal tooling'],
    current: false,
  },
  {
    role: 'Director of Software Engineering',
    company: 'Sports Thread',
    period: 'Jun 2022 — Nov 2023',
    description: 'Set and enforced code standards, development methodologies, and best practices. Built customer-facing and internal tools.',
    highlights: ['Code standards', 'Team practices', 'Customer tools'],
    current: false,
  },
  {
    role: 'Marketing Manager',
    company: 'Sports Thread',
    period: 'Jan 2022 — Jun 2022',
    description: 'Started at Sports Thread in a non-technical role before transitioning into engineering leadership.',
    highlights: ['Automation', 'Process optimization'],
    current: false,
  },
]

const values = [
  {
    icon: '🎯',
    title: 'Ship What Matters',
    description: 'I focus on solving real problems. Every line of code should serve users, not just look clever.',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    icon: '🧹',
    title: 'Clean Architecture',
    description: 'I believe in code that\'s readable, testable, and maintainable. DDD and clean architecture aren\'t buzzwords—they\'re how I build.',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    icon: '📈',
    title: 'Continuous Growth',
    description: 'Tech evolves fast. I stay curious, learn constantly, and share knowledge with my team.',
    gradient: 'from-orange-500 to-red-500',
  },
  {
    icon: '🤝',
    title: 'Team First',
    description: 'Great products come from great teams. I invest in people, foster collaboration, and lead by example.',
    gradient: 'from-green-500 to-teal-500',
  },
]

const education = {
  degree: 'B.S. Computer Science',
  school: 'Colorado Technical University',
  coursework: [
    'Machine Learning',
    'Software Engineering',
    'Computer Algorithms',
    'Big Data Analytics',
    'Database Systems',
    'Operating Systems',
    'Data Structures',
    'Parallel & Distributed Computing',
    'Mobile App Development',
    'Software Quality Assurance',
  ],
}

const certifications = [
  {
    name: 'Certified Scrum Developer (CSD)',
    issuer: 'Scrum Alliance',
    icon: '⚙️',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    name: 'Certified ScrumMaster (CSM)',
    issuer: 'Scrum Alliance',
    icon: '🏅',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    name: 'Certified Scrum Product Owner (CSPO)',
    issuer: 'Scrum Alliance',
    icon: '📋',
    gradient: 'from-orange-500 to-red-500',
  },
  {
    name: 'Django Web Framework',
    issuer: 'Educative',
    icon: '🌐',
    gradient: 'from-green-500 to-teal-500',
  },
  {
    name: 'SQL for Data Science',
    issuer: 'University of California, Davis',
    icon: '📊',
    gradient: 'from-yellow-500 to-orange-500',
  },
]

export default function About() {
  return (
    <>
      <SEO
        title="About Joseph Prince - CTO & Software Engineer"
        description="Joseph Prince is a CTO and Full Stack Software Engineer at Sports Thread, a sports event management platform serving 2M+ users (not the pastor). Grew from Marketing Manager to technical leader in 4 years. Expert in Python, TypeScript, React, Django, and scalable systems."
        canonical="https://www.thejosephprince.com/about"
        tags={['Joseph Prince CTO', 'Joseph Prince Software Engineer', 'Sports Thread CTO', 'Full Stack Developer', 'Technical Leadership', 'Python Developer', 'React Developer']}
      />
      <JsonLd data={generatePersonSchema()} />
      <JsonLd data={generateProfilePageSchema()} />
      <JsonLd data={generateFAQSchema()} />
      <JsonLd data={generateBreadcrumbSchema([
        { name: 'Home', url: '/' },
        { name: 'About', url: '/about' },
      ])} />

      {/* Hero Section */}
      <section className="min-h-[70vh] flex items-center relative overflow-hidden">
        {/* Background gradient orbs - animated like Home page */}
        <div className="absolute top-20 right-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 left-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-full blur-3xl" />
        
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="grid md:grid-cols-5 gap-12 items-center">
            {/* Text content */}
            <div className="md:col-span-3">
              {/* Status badge like Home */}
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-dark-800/80 border border-gray-700 rounded-full mb-8 backdrop-blur-sm">
                <span className="text-blue-400">👋</span>
                <span className="text-sm text-gray-300">About Me</span>
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
                <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                  Building products
                </span>
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  that scale
                </span>
              </h1>
              <p className="text-lg md:text-xl text-gray-400 leading-relaxed mb-8 max-w-xl">
                I'm the CTO at Sports Thread, where I lead engineering for a platform serving 
                over half a million users. I started in a non-technical role and worked my way up—
                <span className="text-white font-medium"> from Marketing Manager to CTO in just 4 years.</span>
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/contact"
                  className="group px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
                >
                  <span className="flex items-center gap-2">
                    Get in Touch
                    <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </span>
                </Link>
                <a
                  href="https://www.linkedin.com/in/thejprince/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 bg-dark-800 hover:bg-dark-700 border border-gray-700 hover:border-blue-500 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  LinkedIn
                </a>
              </div>
            </div>
            
            {/* Stats card - enhanced */}
            <div className="md:col-span-2">
              <div className="relative group">
                {/* Gradient border effect */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500" />
                <div className="relative bg-dark-800/90 backdrop-blur-sm border border-gray-800 rounded-2xl p-8">
                  <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    Quick Facts
                  </h3>
                  <div className="space-y-5">
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-700/50 transition-colors">
                      <span className="text-2xl">💼</span>
                      <div>
                        <p className="text-white font-medium">CTO at Sports Thread</p>
                        <p className="text-gray-500 text-sm">Since 2022</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-700/50 transition-colors">
                      <span className="text-2xl">👥</span>
                      <div>
                        <p className="text-white font-medium">2M+ Users</p>
                        <p className="text-gray-500 text-sm">Platform scale</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-700/50 transition-colors">
                      <span className="text-2xl">🎓</span>
                      <div>
                        <p className="text-white font-medium">B.S. Computer Science</p>
                        <p className="text-gray-500 text-sm">Colorado Technical University</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-700/50 transition-colors">
                      <span className="text-2xl">🚀</span>
                      <div>
                        <p className="text-white font-medium">10+ Projects</p>
                        <p className="text-gray-500 text-sm">Shipped to production</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Experience Timeline */}
      <section className="py-24 relative overflow-hidden">
        {/* Subtle background */}
        <div className="absolute inset-0 bg-gradient-to-b from-dark-800/50 via-transparent to-dark-800/50" />
        
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="text-center mb-16">
            <p className="text-blue-400 font-medium mb-3 text-sm uppercase tracking-wider">Career Journey</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Experience</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              From Marketing Manager to CTO in 4 years—building and scaling a platform for 2M+ users.
            </p>
          </div>

          <div className="space-y-6 max-w-3xl mx-auto">
            {experience.map((job, index) => (
              <div
                key={index}
                className="relative pl-8 border-l-2 border-gray-700 hover:border-blue-500/50 transition-colors duration-300"
              >
                {/* Timeline dot */}
                <div className={`absolute -left-[9px] top-6 w-4 h-4 rounded-full border-2 border-dark-900 ${job.current ? 'bg-blue-500' : 'bg-gray-600'}`}>
                  {job.current && (
                    <span className="absolute inset-0 rounded-full bg-blue-500 animate-ping opacity-50" />
                  )}
                </div>
                
                <div className="group bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-300 hover:-translate-x-1">
                  {/* Gradient accent on hover */}
                  <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-blue-500 to-purple-500 rounded-l-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  
                  <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
                    <div>
                      <h3 className="text-xl font-semibold text-white group-hover:text-blue-400 transition-colors">{job.role}</h3>
                      <p className="text-gray-400">{job.company}</p>
                    </div>
                    <span className="text-sm text-gray-500 bg-dark-700 px-3 py-1 rounded-full">
                      {job.period}
                    </span>
                  </div>
                  <p className="text-gray-400 mb-4 leading-relaxed">{job.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {job.highlights.map((highlight) => (
                      <span
                        key={highlight}
                        className="px-3 py-1 bg-dark-700/80 text-gray-300 text-sm rounded-lg border border-gray-700/50"
                      >
                        {highlight}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-blue-400 font-medium mb-3 text-sm uppercase tracking-wider">Philosophy</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">How I Work</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Principles that guide my engineering and leadership.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <div
                key={value.title}
                className="group relative p-6 bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl transition-all duration-500 hover:-translate-y-2"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Gradient accent on top */}
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${value.gradient} rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />
                
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-r ${value.gradient} mb-4`}>
                  <span className="text-2xl">{value.icon}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300 transition-all">
                  {value.title}
                </h3>
                <p className="text-gray-400 text-sm leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Education Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-dark-800/50 via-transparent to-dark-800/50" />
        
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="text-center mb-16">
            <p className="text-blue-400 font-medium mb-3 text-sm uppercase tracking-wider">Academic Background</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Education</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              A strong foundation in computer science fundamentals, from algorithms to machine learning.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12 items-start">
            <div>
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500" />
                <div className="relative bg-dark-800/90 border border-gray-800 rounded-2xl p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-16 h-16 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                      <span className="text-3xl">🎓</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white">{education.degree}</h3>
                      <p className="text-gray-400">{education.school}</p>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-gray-700">
                    <p className="text-gray-400 text-sm leading-relaxed">
                      Comprehensive program covering software engineering principles, data structures, algorithms, and modern development practices.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <span className="w-2 h-2 bg-purple-500 rounded-full" />
                Relevant Coursework
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {education.coursework.map((course, index) => (
                  <div
                    key={course}
                    className="group px-4 py-3 bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-xl text-gray-300 text-sm transition-all duration-300 hover:-translate-y-0.5 cursor-default"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <span className="group-hover:text-white transition-colors">{course}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Certifications Section */}
      <section className="py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-blue-400 font-medium mb-3 text-sm uppercase tracking-wider">Professional Development</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Certifications</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Professional certifications in development, databases, and agile methodologies.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-6">
            {certifications.map((cert, index) => (
              <div
                key={cert.name}
                className="group relative p-6 bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl transition-all duration-500 hover:-translate-y-2 w-full md:w-[calc(50%-12px)] lg:w-[calc(33.333%-16px)]"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Gradient accent on top */}
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${cert.gradient} rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />
                
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${cert.gradient} flex items-center justify-center flex-shrink-0`}>
                    <span className="text-xl">{cert.icon}</span>
                  </div>
                  <div>
                    <h3 className="text-white font-medium group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300 transition-all mb-1">
                      {cert.name}
                    </h3>
                    <p className="text-gray-500 text-sm">{cert.issuer}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6">
          <div className="relative group">
            {/* Outer glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 rounded-3xl blur-xl opacity-20 group-hover:opacity-40 transition duration-500" />
            
            <div className="relative p-10 md:p-16 bg-dark-800/90 border border-gray-700 rounded-3xl text-center overflow-hidden">
              {/* Background orbs */}
              <div className="absolute top-0 left-1/4 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
              <div className="absolute bottom-0 right-1/4 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
              
              <div className="relative z-10">
                <h2 className="text-3xl md:text-4xl font-bold mb-4">
                  <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                    Want to Work Together?
                  </span>
                </h2>
                <p className="text-gray-400 mb-8 max-w-lg mx-auto text-lg">
                  I'm always open to discussing new projects, consulting opportunities, or just talking tech.
                </p>
                <Link
                  to="/contact"
                  className="group/btn inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all duration-300 hover:-translate-y-0.5 shadow-xl shadow-blue-500/25"
                >
                  Start a Conversation
                  <svg className="w-5 h-5 transition-transform group-hover/btn:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
