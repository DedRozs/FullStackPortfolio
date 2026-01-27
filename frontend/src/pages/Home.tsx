import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  tags: string[]
  published_at: string
  read_time: number
}

export default function Home() {
  const [recentPosts, setRecentPosts] = useState<BlogPost[]>([])
  const [loading, setLoading] = useState(true)

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
      {/* Hero Section */}
      <section className="min-h-[80vh] flex items-center">
        <div className="max-w-6xl mx-auto px-6">
          <div className="max-w-3xl">
            <p className="text-blue-400 font-medium mb-4">Hi, I'm</p>
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
              Joseph Prince
            </h1>
            <p className="text-xl md:text-2xl text-gray-400 mb-8 leading-relaxed">
              CTO at <span className="text-white">Sports Thread</span>. 
              From building{' '}
              <span className="text-white">scalable REST APIs</span> to leading{' '}
              <span className="text-white">engineering teams</span>—I ship products that matter.
            </p>
            <div className="flex gap-4">
              <Link
                to="/blog"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition"
              >
                Read the Blog
              </Link>
              <Link
                to="/contact"
                className="px-6 py-3 border border-gray-600 hover:border-gray-400 text-white font-medium rounded-lg transition"
              >
                Get in Touch
              </Link>
            </div>
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
                  className="bg-dark-800 rounded-xl p-6 hover:bg-dark-700 transition group"
                >
                  <Link to={`/blog/${post.slug}`}>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {post.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-dark-600 text-blue-400 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition">
                      {post.title}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                      {post.excerpt}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <time dateTime={post.published_at}>
                        {formatDate(post.published_at)}
                      </time>
                      <span>{post.read_time} min read</span>
                    </div>
                  </Link>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  )
}
