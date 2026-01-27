export default function About() {
  const skills = [
    'Python',
    'Django',
    'React',
    'TypeScript',
    'Google Cloud',
    'REST APIs',
    'GitHub Actions',
    'PostgreSQL',
    'SQL',
    'Machine Learning',
    'Leadership',
  ]

  return (
    <section className="py-16">
      <div className="max-w-6xl mx-auto px-6">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-8">About Me</h1>

        <div className="grid md:grid-cols-3 gap-12">
          {/* Main content */}
          <div className="md:col-span-2 space-y-6">
            <p className="text-lg text-gray-300 leading-relaxed">
              I'm the Chief Technical Officer at Sports Thread, a SaaS platform
              in the sports industry. I started as a Full-Stack Developer,
              building internal tools that streamlined customer service
              workflows—significantly reducing processing time and improving
              operational efficiency. That hands-on experience designing
              scalable REST APIs, optimizing backend performance, and automating
              deployments laid the foundation for where I am today.
            </p>
            <p className="text-lg text-gray-300 leading-relaxed">
              My expertise is rooted in Django, Python, and Google Cloud, with a
              strong focus on CI/CD pipelines using GitHub Actions. I thrive in
              fast-paced SaaS environments, solving complex engineering problems
              and collaborating with cross-functional teams to deliver
              high-performance solutions.
            </p>
            <p className="text-lg text-gray-300 leading-relaxed">
              Now as CTO, I combine that technical depth with leadership—growing
              teams, setting technical direction, and ensuring we ship products
              that actually matter to our users.
            </p>

            {/* Skills section */}
            <div className="pt-8">
              <h2 className="text-2xl font-semibold text-white mb-6">Skills & Tech</h2>
              <div className="flex flex-wrap gap-3">
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-4 py-2 bg-dark-700 text-gray-300 rounded-lg"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            <div className="bg-dark-800 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Quick Facts</h3>
              <ul className="space-y-3 text-gray-400">
                <li>💼 CTO at Sports Thread</li>
                <li>🎓 B.S. Computer Science</li>
                <li>🚀 3+ years in Full-Stack Development</li>
                <li>☁️ Google Cloud & DevOps</li>
              </ul>
            </div>

            <div className="bg-dark-800 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Coursework Highlights</h3>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>• Machine Learning</li>
                <li>• Software Engineering</li>
                <li>• Computer Algorithms</li>
                <li>• Big Data Analytics</li>
                <li>• Database Systems & SQL</li>
                <li>• Operating Systems</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
