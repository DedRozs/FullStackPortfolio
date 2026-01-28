import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { marked } from 'marked'
import SEO, { JsonLd, generateBlogPostSchema, generateBreadcrumbSchema } from '../components/SEO'

interface PriceLevel {
  type: string
  type_name: string
  price: number
}

interface TradingPost {
  id: string
  instrument: string
  instrument_name: string
  post_type: string
  post_type_name: string
  title: string
  slug: string
  content: string
  excerpt: string
  session_date: string
  status: string
  reading_time: number
  created_at: string
  updated_at: string
  published_at: string | null
  scheduled_for: string | null
  meta_description: string | null
  price_levels: PriceLevel[]
}

// Instrument-specific gradients for visual distinction
const instrumentGradients: Record<string, string> = {
  NQ: 'from-cyan-500 to-blue-500',
  ES: 'from-green-500 to-emerald-500',
  RTY: 'from-orange-500 to-amber-500',
  YM: 'from-purple-500 to-violet-500',
}

// Post type icons
const postTypeIcons: Record<string, string> = {
  PRE_MARKET: '🌅',
  POST_MARKET: '🌙',
  WEEKLY_RECAP: '📊',
}

// Post type gradients
const postTypeGradients: Record<string, string> = {
  PRE_MARKET: 'from-amber-500 to-orange-500',
  POST_MARKET: 'from-indigo-500 to-purple-500',
  WEEKLY_RECAP: 'from-teal-500 to-cyan-500',
}

export default function TradingBlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const [post, setPost] = useState<TradingPost | null>(null)
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
        const response = await fetch(`/api/trading/posts/${slug}/`)
        if (response.ok) {
          const data = await response.json()
          setPost(data.post)
        } else if (response.status === 404) {
          setError('Post not found')
        } else {
          setError('Failed to load post')
        }
      } catch (err) {
        console.error('Error fetching trading post:', err)
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
      day: 'numeric',
    })
  }

  const formatSessionDate = (dateString: string) => {
    // Parse YYYY-MM-DD without timezone conversion
    const [year, month, day] = dateString.split('-').map(Number)
    const date = new Date(year, month - 1, day)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatPrice = (price: number) => {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  const getInstrumentGradient = (instrument: string) => {
    return instrumentGradients[instrument] || 'from-gray-500 to-gray-600'
  }

  const getPostTypeGradient = (postType: string) => {
    return postTypeGradients[postType] || 'from-gray-500 to-gray-600'
  }

  const getPostTypeIcon = (postType: string) => {
    return postTypeIcons[postType] || '📝'
  }

  if (loading) {
    return (
      <>
        {/* Loading Hero */}
        <section className="min-h-[40vh] flex items-center relative overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-green-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000" />

          <div className="max-w-4xl mx-auto px-6 relative z-10 w-full">
            <div className="animate-pulse">
              <div className="flex gap-3 mb-6">
                <div className="h-8 w-14 bg-dark-700 rounded-lg"></div>
                <div className="h-7 w-28 bg-dark-700 rounded-full"></div>
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
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000" />

        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <div className="relative inline-block mb-8">
            <div className="absolute -inset-4 bg-gradient-to-r from-red-500/20 to-cyan-500/20 rounded-full blur-xl" />
            <div className="relative w-24 h-24 rounded-full bg-dark-800 border border-gray-700 flex items-center justify-center mx-auto">
              <span className="text-5xl">📊</span>
            </div>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              {error || 'Post not found'}
            </span>
          </h1>
          <p className="text-lg text-gray-400 mb-10 max-w-md mx-auto">
            The trading analysis you're looking for doesn't exist or has been removed.
          </p>
          <Link
            to="/trading-blog"
            className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-600 to-cyan-500 hover:from-green-500 hover:to-cyan-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-green-500/25 hover:shadow-green-500/40 hover:-translate-y-0.5"
          >
            <svg className="w-4 h-4 transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
            Back to Trading Blog
          </Link>
        </div>
      </section>
    )
  }

  return (
    <>
      <SEO
        title={post.title}
        description={post.meta_description || post.excerpt}
        canonical={`https://www.thejosephprince.com/trading-blog/${post.slug}`}
        type="article"
        image={`https://www.thejosephprince.com/static/og-images/trading-${post.slug}.png`}
        imageAlt={post.title}
        publishedTime={post.published_at || post.created_at}
        modifiedTime={post.updated_at}
        tags={[post.instrument_name, post.post_type_name, 'Futures Trading', 'Technical Analysis']}
      />
      <JsonLd data={generateBlogPostSchema({
        title: post.title,
        description: post.meta_description || post.excerpt,
        slug: `trading-blog/${post.slug}`,
        publishedAt: post.published_at || post.created_at,
        modifiedAt: post.updated_at,
        tags: [post.instrument_name, post.post_type_name],
        readingTime: post.reading_time,
      })} />
      <JsonLd data={generateBreadcrumbSchema([
        { name: 'Home', url: '/' },
        { name: 'Trading Blog', url: '/trading-blog' },
        { name: post.title, url: `/trading-blog/${post.slug}` },
      ])} />

      {/* Hero Section */}
      <section className="min-h-[40vh] flex items-end relative overflow-hidden pb-16">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-green-500/5 to-cyan-500/5 rounded-full blur-3xl" />

        <div className="max-w-4xl mx-auto px-6 relative z-10 w-full">
          {/* Back Link */}
          <Link
            to="/trading-blog"
            className="group inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8"
          >
            <svg className="w-4 h-4 transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
            Back to Trading Blog
          </Link>

          {/* Instrument and Post Type badges */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <span
              className={`px-4 py-2 text-base font-bold rounded-xl bg-gradient-to-r ${getInstrumentGradient(post.instrument)} text-white`}
            >
              {post.instrument}
            </span>
            <span
              className={`px-4 py-1.5 text-sm font-medium rounded-full bg-gradient-to-r ${getPostTypeGradient(post.post_type)} text-white flex items-center gap-2`}
            >
              <span>{getPostTypeIcon(post.post_type)}</span>
              {post.post_type_name}
            </span>
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
              <time>
                {formatSessionDate(post.session_date)}
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

      {/* Price Levels Table (if available) */}
      {post.price_levels && post.price_levels.length > 0 && (
        <section className="py-8">
          <div className="max-w-4xl mx-auto px-6">
            <div className="bg-dark-800/50 border border-gray-800 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Key Price Levels
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Level Type</th>
                      <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {post.price_levels.map((level, index) => (
                      <tr
                        key={level.type}
                        className={`${index % 2 === 0 ? 'bg-dark-900/30' : ''}`}
                      >
                        <td className="py-3 px-4 text-gray-300">{level.type_name}</td>
                        <td className="py-3 px-4 text-right font-mono text-white">
                          {formatPrice(level.price)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

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
              prose-a:text-green-400 prose-a:no-underline prose-a:font-medium hover:prose-a:text-green-300 hover:prose-a:underline
              prose-strong:text-white prose-strong:font-semibold
              prose-code:text-green-400 prose-code:bg-dark-800 prose-code:px-2 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-code:font-mono
              prose-pre:bg-dark-800 prose-pre:border prose-pre:border-gray-700 prose-pre:rounded-xl prose-pre:p-6
              prose-blockquote:border-l-4 prose-blockquote:border-green-500 prose-blockquote:bg-dark-800/50 prose-blockquote:rounded-r-xl prose-blockquote:py-4 prose-blockquote:px-6 prose-blockquote:text-gray-300 prose-blockquote:not-italic
              prose-ul:text-gray-300 prose-ol:text-gray-300 prose-ul:my-6 prose-ol:my-6
              prose-li:marker:text-green-400 prose-li:mb-2
              prose-img:rounded-xl prose-img:shadow-lg prose-img:border prose-img:border-gray-800
              prose-hr:border-gray-800 prose-hr:my-12
              prose-table:border-collapse prose-table:w-full
              prose-th:bg-dark-800 prose-th:text-gray-300 prose-th:py-3 prose-th:px-4 prose-th:text-left prose-th:border prose-th:border-gray-700
              prose-td:py-3 prose-td:px-4 prose-td:border prose-td:border-gray-700 prose-td:text-gray-300"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        </div>
      </article>

      {/* Disclaimer */}
      <section className="pb-16">
        <div className="max-w-4xl mx-auto px-6">
          <div className="bg-amber-900/20 border border-amber-700/50 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-amber-400 font-semibold mb-2">Trading Disclaimer</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  This analysis is for educational purposes only and does not constitute financial advice.
                  Futures trading involves substantial risk of loss and is not suitable for all investors.
                  Past performance is not indicative of future results. Always conduct your own research
                  and consult with a licensed financial advisor before making trading decisions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <section className="py-16 border-t border-gray-800">
        <div className="max-w-4xl mx-auto px-6">
          {/* Share and meta */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-16">
            <div className="flex items-center gap-3 text-gray-500">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Updated on {formatDate(post.updated_at)}</span>
            </div>

            <div className="flex gap-3">
              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(window.location.href)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group px-5 py-2.5 bg-dark-800 border border-gray-800 text-gray-300 rounded-xl hover:bg-dark-700 hover:border-gray-600 transition-all duration-300 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                Share on X
              </a>
            </div>
          </div>

          {/* Navigation Cards */}
          <div className="grid md:grid-cols-2 gap-6 mb-16">
            {/* View more for this instrument */}
            <Link
              to={`/trading-blog?instrument=${post.instrument}`}
              className="group relative bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <span
                  className={`px-3 py-1.5 text-sm font-bold rounded-lg bg-gradient-to-r ${getInstrumentGradient(post.instrument)} text-white`}
                >
                  {post.instrument}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">More {post.instrument_name} Analysis</h3>
              <p className="text-gray-400 text-sm">View all pre-market and recap posts for {post.instrument}</p>
              <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </div>
            </Link>

            {/* View more of this post type */}
            <Link
              to={`/trading-blog?type=${post.post_type}`}
              className="group relative bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <span
                  className={`px-3 py-1 text-sm font-medium rounded-full bg-gradient-to-r ${getPostTypeGradient(post.post_type)} text-white flex items-center gap-1`}
                >
                  <span>{getPostTypeIcon(post.post_type)}</span>
                  {post.post_type_name}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">More {post.post_type_name} Posts</h3>
              <p className="text-gray-400 text-sm">Browse all {post.post_type_name.toLowerCase()} analysis across instruments</p>
              <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </div>
            </Link>
          </div>

          {/* CTA Card */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-green-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
            <div className="relative bg-dark-800/90 border border-gray-800 rounded-2xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Want more analysis?</h3>
                  <p className="text-gray-400">Subscribe to the RSS feed or explore all trading insights.</p>
                </div>
                <div className="flex flex-wrap gap-4">
                  <Link
                    to="/trading-blog"
                    className="px-6 py-3 bg-dark-700 hover:bg-dark-600 border border-gray-700 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5"
                  >
                    All Analysis
                  </Link>
                  <a
                    href="/api/trading/rss/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group/btn px-6 py-3 bg-gradient-to-r from-green-600 to-cyan-500 hover:from-green-500 hover:to-cyan-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-green-500/25 hover:shadow-green-500/40 hover:-translate-y-0.5 flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19 7.38 20 6.18 20C5 20 4 19 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1Z" />
                    </svg>
                    RSS Feed
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
