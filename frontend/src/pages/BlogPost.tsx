import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { marked } from 'marked'

interface BlogPost {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string
  tags: string[]
  status: string
  published_at: string | null
  created_at: string
  updated_at: string
  reading_time: number
}

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const [post, setPost] = useState<BlogPost | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Parse markdown to HTML
  const htmlContent = useMemo(() => {
    if (!post?.content) return ''
    // Remove the first heading (title) since it's already in the header
    const contentWithoutTitle = post.content.replace(/^#\s+.+\n+/, '')
    return marked.parse(contentWithoutTitle) as string
  }, [post?.content])

  useEffect(() => {
    const fetchPost = async () => {
      if (!slug) return

      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`/api/blog/posts/${slug}/`)
        if (response.ok) {
          const data = await response.json()
          setPost(data.post)
        } else if (response.status === 404) {
          setError('Post not found')
        } else {
          setError('Failed to load post')
        }
      } catch (err) {
        console.error('Error fetching post:', err)
        setError('Failed to load post')
      } finally {
        setLoading(false)
      }
    }

    fetchPost()
  }, [slug])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Tag color variants for visual interest
  const tagGradients = [
    'from-blue-500 to-cyan-500',
    'from-purple-500 to-pink-500',
    'from-orange-500 to-red-500',
    'from-green-500 to-teal-500',
    'from-yellow-500 to-orange-500',
  ]

  const getTagGradient = (tag: string) => {
    const index = tag.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return tagGradients[index % tagGradients.length]
  }

  if (loading) {
    return (
      <>
        {/* Loading Hero */}
        <section className="min-h-[40vh] flex items-center relative overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
          
          <div className="max-w-4xl mx-auto px-6 relative z-10 w-full">
            <div className="animate-pulse">
              <div className="flex gap-3 mb-6">
                <div className="h-7 w-20 bg-dark-700 rounded-full"></div>
                <div className="h-7 w-24 bg-dark-700 rounded-full"></div>
              </div>
              <div className="h-14 bg-dark-700 rounded-xl w-4/5 mb-4"></div>
              <div className="h-14 bg-dark-700 rounded-xl w-3/5 mb-8"></div>
              <div className="flex gap-6">
                <div className="h-5 bg-dark-700 rounded w-32"></div>
                <div className="h-5 bg-dark-700 rounded w-24"></div>
              </div>
            </div>
          </div>
        </section>
        
        {/* Loading Content */}
        <section className="py-16">
          <div className="max-w-4xl mx-auto px-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-dark-700 rounded w-full"></div>
              <div className="h-4 bg-dark-700 rounded w-full"></div>
              <div className="h-4 bg-dark-700 rounded w-5/6"></div>
              <div className="h-4 bg-dark-700 rounded w-full"></div>
              <div className="h-4 bg-dark-700 rounded w-4/5"></div>
              <div className="h-8 bg-dark-700 rounded w-2/5 mt-8"></div>
              <div className="h-4 bg-dark-700 rounded w-full"></div>
              <div className="h-4 bg-dark-700 rounded w-full"></div>
              <div className="h-4 bg-dark-700 rounded w-3/4"></div>
            </div>
          </div>
        </section>
      </>
    )
  }

  if (error || !post) {
    return (
      <section className="min-h-[70vh] flex items-center relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-red-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <div className="relative inline-block mb-8">
            <div className="absolute -inset-4 bg-gradient-to-r from-red-500/20 to-purple-500/20 rounded-full blur-xl" />
            <div className="relative w-24 h-24 rounded-full bg-dark-800 border border-gray-700 flex items-center justify-center mx-auto">
              <span className="text-5xl">📄</span>
            </div>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              {error || 'Post not found'}
            </span>
          </h1>
          <p className="text-lg text-gray-400 mb-10 max-w-md mx-auto">
            The blog post you're looking for doesn't exist or has been removed.
          </p>
          <Link
            to="/blog"
            className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
          >
            <svg className="w-4 h-4 transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
            Back to Blog
          </Link>
        </div>
      </section>
    )
  }

  return (
    <>
      {/* Hero Section */}
      <section className="min-h-[40vh] flex items-end relative overflow-hidden pb-16">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-full blur-3xl" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 w-full">
          {/* Back Link */}
          <Link
            to="/blog"
            className="group inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8"
          >
            <svg className="w-4 h-4 transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
            Back to Blog
          </Link>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-6">
            {(post.tags || []).map((tag) => (
              <Link
                key={tag}
                to={`/blog?tag=${encodeURIComponent(tag)}`}
                className={`px-4 py-1.5 text-sm font-medium rounded-full bg-gradient-to-r ${getTagGradient(tag)} text-white hover:opacity-90 transition-opacity`}
              >
                {tag}
              </Link>
            ))}
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-8 leading-tight">
            <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              {post.title}
            </span>
          </h1>

          {/* Meta info */}
          <div className="flex flex-wrap items-center gap-6 text-gray-400">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <time dateTime={post.published_at || post.created_at}>
                {formatDate(post.published_at || post.created_at)}
              </time>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{post.reading_time} min read</span>
            </div>
          </div>
        </div>
      </section>

      {/* Content Section */}
      <article className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          {/* Article content */}
          <div 
            className="prose prose-invert prose-lg max-w-none
              prose-headings:text-white prose-headings:font-bold prose-headings:tracking-tight
              prose-h2:text-3xl prose-h2:mt-12 prose-h2:mb-6 prose-h2:pb-4 prose-h2:border-b prose-h2:border-gray-800
              prose-h3:text-2xl prose-h3:mt-10 prose-h3:mb-4
              prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-6
              prose-a:text-blue-400 prose-a:no-underline prose-a:font-medium hover:prose-a:text-blue-300 hover:prose-a:underline
              prose-strong:text-white prose-strong:font-semibold
              prose-code:text-blue-400 prose-code:bg-dark-800 prose-code:px-2 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-code:font-mono
              prose-pre:bg-dark-800 prose-pre:border prose-pre:border-gray-700 prose-pre:rounded-xl prose-pre:p-6
              prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-dark-800/50 prose-blockquote:rounded-r-xl prose-blockquote:py-4 prose-blockquote:px-6 prose-blockquote:text-gray-300 prose-blockquote:not-italic
              prose-ul:text-gray-300 prose-ol:text-gray-300 prose-ul:my-6 prose-ol:my-6
              prose-li:marker:text-blue-400 prose-li:mb-2
              prose-img:rounded-xl prose-img:shadow-lg prose-img:border prose-img:border-gray-800
              prose-hr:border-gray-800 prose-hr:my-12"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        </div>
      </article>

      {/* Footer Section */}
      <section className="py-16 border-t border-gray-800">
        <div className="max-w-4xl mx-auto px-6">
          {/* Share and meta */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-16">
            <div className="flex items-center gap-3 text-gray-500">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Last updated on {formatDate(post.updated_at)}</span>
            </div>
            
            <div className="flex gap-3">
              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(window.location.href)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group px-5 py-2.5 bg-dark-800 border border-gray-800 text-gray-300 rounded-xl hover:bg-dark-700 hover:border-gray-600 transition-all duration-300 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Share on X
              </a>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group px-5 py-2.5 bg-dark-800 border border-gray-800 text-gray-300 rounded-xl hover:bg-dark-700 hover:border-gray-600 transition-all duration-300 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                Share
              </a>
            </div>
          </div>

          {/* CTA Card */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
            <div className="relative bg-dark-800/90 border border-gray-800 rounded-2xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Enjoyed this article?</h3>
                  <p className="text-gray-400">Check out more posts or get in touch to discuss ideas.</p>
                </div>
                <div className="flex flex-wrap gap-4">
                  <Link
                    to="/blog"
                    className="px-6 py-3 bg-dark-700 hover:bg-dark-600 border border-gray-700 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5"
                  >
                    More Articles
                  </Link>
                  <Link
                    to="/contact"
                    className="group/btn px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 flex items-center gap-2"
                  >
                    Get in Touch
                    <svg className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
