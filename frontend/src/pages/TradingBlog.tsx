import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import SEO, { JsonLd, generateBreadcrumbSchema } from '../components/SEO'

interface TradingPost {
  id: string
  instrument: string
  instrument_name: string
  post_type: string
  post_type_name: string
  title: string
  slug: string
  excerpt: string
  session_date: string
  reading_time: number
  published_at: string | null
}

interface Instrument {
  symbol: string
  short_name: string
  display_name: string
}

interface PostType {
  value: string
  name: string
}

interface TradingBlogResponse {
  posts: TradingPost[]
  total: number
  page: number
  page_size: number
  total_pages: number
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

export default function TradingBlog() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [posts, setPosts] = useState<TradingPost[]>([])
  const [instruments, setInstruments] = useState<Instrument[]>([])
  const [postTypes, setPostTypes] = useState<PostType[]>([])
  const [loading, setLoading] = useState(true)
  const [totalPages, setTotalPages] = useState(1)

  const currentPage = parseInt(searchParams.get('page') || '1')
  const currentInstrument = searchParams.get('instrument') || ''
  const currentPostType = searchParams.get('type') || ''

  // Fetch posts with filters
  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true)
      try {
        let url = `/api/trading/posts/?page=${currentPage}`
        if (currentInstrument) {
          url += `&instrument=${encodeURIComponent(currentInstrument)}`
        }
        if (currentPostType) {
          url += `&type=${encodeURIComponent(currentPostType)}`
        }

        const response = await fetch(url)
        if (response.ok) {
          const data: TradingBlogResponse = await response.json()
          setPosts(data.posts || [])
          setTotalPages(data.total_pages || 1)
        }
      } catch (error) {
        console.error('Error fetching trading posts:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPosts()
  }, [currentPage, currentInstrument, currentPostType])

  // Fetch instruments
  useEffect(() => {
    const fetchInstruments = async () => {
      try {
        const response = await fetch('/api/trading/instruments/')
        if (response.ok) {
          const data = await response.json()
          setInstruments(data.instruments || [])
        }
      } catch (error) {
        console.error('Error fetching instruments:', error)
      }
    }

    fetchInstruments()
  }, [])

  // Fetch post types
  useEffect(() => {
    const fetchPostTypes = async () => {
      try {
        const response = await fetch('/api/trading/types/')
        if (response.ok) {
          const data = await response.json()
          setPostTypes(data.post_types || [])
        }
      } catch (error) {
        console.error('Error fetching post types:', error)
      }
    }

    fetchPostTypes()
  }, [])

  const handleInstrumentChange = useCallback((instrument: string) => {
    if (instrument === currentInstrument) {
      searchParams.delete('instrument')
    } else if (instrument) {
      searchParams.set('instrument', instrument)
    } else {
      searchParams.delete('instrument')
    }
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }, [currentInstrument, searchParams, setSearchParams])

  const handlePostTypeChange = useCallback((postType: string) => {
    if (postType === currentPostType) {
      searchParams.delete('type')
    } else if (postType) {
      searchParams.set('type', postType)
    } else {
      searchParams.delete('type')
    }
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }, [currentPostType, searchParams, setSearchParams])

  const clearAllFilters = useCallback(() => {
    searchParams.delete('instrument')
    searchParams.delete('type')
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }, [searchParams, setSearchParams])

  const handlePageChange = useCallback((page: number) => {
    searchParams.set('page', page.toString())
    setSearchParams(searchParams)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [searchParams, setSearchParams])

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
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
  }

  const hasActiveFilters = currentInstrument || currentPostType

  const getInstrumentGradient = (instrument: string) => {
    return instrumentGradients[instrument] || 'from-gray-500 to-gray-600'
  }

  const getPostTypeGradient = (postType: string) => {
    return postTypeGradients[postType] || 'from-gray-500 to-gray-600'
  }

  const getPostTypeIcon = (postType: string) => {
    return postTypeIcons[postType] || '📝'
  }

  return (
    <>
      <SEO
        title="Trading Blog"
        description="Daily pre-market analysis and post-market recaps for index futures: NQ, ES, RTY, and YM. Technical levels, overnight session analysis, and trading insights."
        canonical="https://www.thejosephprince.com/trading-blog"
        tags={['Futures Trading', 'NQ', 'ES', 'RTY', 'YM', 'Technical Analysis', 'Pre-Market', 'Market Recap']}
      />
      <JsonLd data={generateBreadcrumbSchema([
        { name: 'Home', url: '/' },
        { name: 'Trading Blog', url: '/trading-blog' },
      ])} />

      {/* Hero Section */}
      <section className="min-h-[50vh] flex items-center relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-green-500/5 to-cyan-500/5 rounded-full blur-3xl" />

        <div className="max-w-6xl mx-auto px-6 relative z-10 w-full">
          <div className="max-w-3xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-dark-800/80 border border-gray-700 rounded-full mb-8 backdrop-blur-sm">
              <span className="text-green-400">📈</span>
              <span className="text-sm text-gray-300">Futures Trading Blog</span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                Market
              </span>
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-cyan-400">
                Analysis
              </span>
            </h1>
            <p className="text-lg md:text-xl text-gray-400 leading-relaxed max-w-2xl">
              Daily pre-market levels and post-market recaps for index futures.
              Technical analysis for NQ, ES, RTY, and YM traders.
            </p>
          </div>
        </div>
      </section>

      {/* Posts Section */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          {/* Filters */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 mb-10">
            {/* Instrument Filters */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleInstrumentChange('')}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                  !currentInstrument
                    ? 'bg-gradient-to-r from-green-600 to-cyan-500 text-white shadow-lg shadow-green-500/25'
                    : 'bg-dark-800 border border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'
                }`}
              >
                All Instruments
              </button>
              {instruments.map((instrument) => (
                <button
                  key={instrument.symbol}
                  onClick={() => handleInstrumentChange(instrument.short_name)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                    currentInstrument === instrument.short_name
                      ? `bg-gradient-to-r ${getInstrumentGradient(instrument.short_name)} text-white shadow-lg`
                      : 'bg-dark-800 border border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'
                  }`}
                >
                  {instrument.short_name}
                </button>
              ))}
            </div>

            {/* Post Type Filter */}
            {postTypes.length > 0 && (
              <div className="lg:ml-auto">
                <select
                  value={currentPostType}
                  onChange={(e) => handlePostTypeChange(e.target.value)}
                  className="appearance-none bg-dark-800 border border-gray-700 hover:border-gray-600 text-gray-300 pl-4 pr-10 py-3 rounded-xl text-sm font-medium focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors cursor-pointer min-w-[160px]"
                >
                  <option value="">All Post Types</option>
                  {postTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={clearAllFilters}
                className="px-4 py-3 text-sm text-gray-400 hover:text-white bg-dark-800 border border-gray-700 hover:border-gray-600 rounded-xl transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Clear
              </button>
            )}
          </div>

          {/* Results Header */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-white">
              {currentInstrument && currentPostType ? (
                <>
                  <span className={`text-transparent bg-clip-text bg-gradient-to-r ${getInstrumentGradient(currentInstrument)}`}>
                    {currentInstrument}
                  </span>
                  {' '}
                  <span className={`text-transparent bg-clip-text bg-gradient-to-r ${getPostTypeGradient(currentPostType)}`}>
                    {postTypes.find(t => t.value === currentPostType)?.name || currentPostType}
                  </span>
                </>
              ) : currentInstrument ? (
                <>
                  <span className={`text-transparent bg-clip-text bg-gradient-to-r ${getInstrumentGradient(currentInstrument)}`}>
                    {currentInstrument}
                  </span>
                  {' Analysis'}
                </>
              ) : currentPostType ? (
                <span className={`text-transparent bg-clip-text bg-gradient-to-r ${getPostTypeGradient(currentPostType)}`}>
                  {postTypes.find(t => t.value === currentPostType)?.name || currentPostType}
                </span>
              ) : (
                'Latest Analysis'
              )}
            </h2>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="grid gap-6 md:grid-cols-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="group relative bg-dark-800/50 border border-gray-800 rounded-2xl p-6 animate-pulse"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-8 w-12 bg-dark-700 rounded-lg"></div>
                    <div className="h-6 w-24 bg-dark-700 rounded-full"></div>
                  </div>
                  <div className="h-7 bg-dark-700 rounded-lg w-4/5 mb-4"></div>
                  <div className="space-y-2 mb-6">
                    <div className="h-4 bg-dark-700 rounded w-full"></div>
                    <div className="h-4 bg-dark-700 rounded w-5/6"></div>
                  </div>
                  <div className="flex justify-between">
                    <div className="h-4 bg-dark-700 rounded w-24"></div>
                    <div className="h-4 bg-dark-700 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : posts.length === 0 ? (
            /* Empty State */
            <div className="text-center py-20">
              <div className="relative inline-block">
                <div className="absolute -inset-4 bg-gradient-to-r from-green-500/20 to-cyan-500/20 rounded-full blur-xl" />
                <div className="relative w-20 h-20 rounded-full bg-dark-800 border border-gray-700 flex items-center justify-center mx-auto mb-6">
                  <span className="text-4xl">📊</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">
                {hasActiveFilters
                  ? 'No posts match your filters'
                  : 'No analysis posts yet'}
              </h3>
              <p className="text-gray-400 mb-8 max-w-md mx-auto">
                {hasActiveFilters
                  ? 'Try adjusting your filters or browse all posts.'
                  : 'Check back soon for daily market analysis.'}
              </p>
              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="px-6 py-3 bg-gradient-to-r from-green-600 to-cyan-500 hover:from-green-500 hover:to-cyan-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-green-500/25 hover:shadow-green-500/40"
                >
                  View All Posts
                </button>
              )}
            </div>
          ) : (
            /* Posts Grid */
            <div className="grid gap-6 md:grid-cols-2">
              {posts.map((post, index) => (
                <article
                  key={post.id}
                  className="group relative bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-500 hover:-translate-y-1"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Gradient accent on hover */}
                  <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${getInstrumentGradient(post.instrument)} rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />

                  <Link to={`/trading-blog/${post.slug}`} className="block">
                    {/* Header: Instrument + Post Type */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-3 py-1.5 text-sm font-bold rounded-lg bg-gradient-to-r ${getInstrumentGradient(post.instrument)} text-white`}
                        >
                          {post.instrument}
                        </span>
                        <span
                          className={`px-3 py-1 text-xs font-medium rounded-full bg-gradient-to-r ${getPostTypeGradient(post.post_type)} text-white flex items-center gap-1`}
                        >
                          <span>{getPostTypeIcon(post.post_type)}</span>
                          {post.post_type_name}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {formatSessionDate(post.session_date)}
                      </span>
                    </div>

                    {/* Title */}
                    <h2 className="text-xl font-semibold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-green-400 group-hover:to-cyan-400 transition-all duration-300 line-clamp-2">
                      {post.title}
                    </h2>

                    {/* Excerpt */}
                    <p className="text-gray-400 text-sm leading-relaxed mb-6 line-clamp-2">
                      {post.excerpt}
                    </p>

                    {/* Meta info */}
                    <div className="flex items-center justify-between text-sm">
                      {post.published_at && (
                        <time dateTime={post.published_at} className="text-gray-500">
                          {formatDate(post.published_at)}
                        </time>
                      )}
                      <span className="flex items-center gap-1.5 text-gray-500">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {post.reading_time} min
                      </span>
                    </div>

                    {/* Read more indicator */}
                    <div className="mt-6 pt-4 border-t border-gray-800 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-green-400 text-sm font-medium">Read analysis</span>
                      <svg className="w-4 h-4 text-green-400 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </div>
                  </Link>
                </article>
              ))}
            </div>
          )}

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <nav className="mt-16 flex justify-center items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="group px-5 py-2.5 bg-dark-800 border border-gray-800 text-gray-300 rounded-xl hover:bg-dark-700 hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-dark-800 disabled:hover:border-gray-800 transition-all duration-300 flex items-center gap-2"
              >
                <svg className="w-4 h-4 transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                </svg>
                Previous
              </button>

              <div className="flex gap-2 px-4">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`w-10 h-10 rounded-xl font-medium transition-all duration-300 ${
                      page === currentPage
                        ? 'bg-gradient-to-r from-green-600 to-cyan-500 text-white shadow-lg shadow-green-500/25'
                        : 'bg-dark-800 border border-gray-800 text-gray-400 hover:bg-dark-700 hover:border-gray-600 hover:text-white'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="group px-5 py-2.5 bg-dark-800 border border-gray-800 text-gray-300 rounded-xl hover:bg-dark-700 hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-dark-800 disabled:hover:border-gray-800 transition-all duration-300 flex items-center gap-2"
              >
                Next
                <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </button>
            </nav>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="relative group">
            {/* Gradient border effect */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-green-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
            <div className="relative bg-dark-800/90 border border-gray-800 rounded-2xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Stay Updated</h3>
                  <p className="text-gray-400">Get daily market analysis delivered via RSS feed.</p>
                </div>
                <div className="flex flex-wrap gap-4">
                  <a
                    href="/api/trading/rss/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group/btn px-8 py-4 bg-gradient-to-r from-green-600 to-cyan-500 hover:from-green-500 hover:to-cyan-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-green-500/25 hover:shadow-green-500/40 hover:-translate-y-0.5 whitespace-nowrap flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19 7.38 20 6.18 20C5 20 4 19 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1Z" />
                    </svg>
                    RSS Feed
                  </a>
                  <Link
                    to="/blog"
                    className="px-6 py-4 bg-dark-700 hover:bg-dark-600 border border-gray-700 text-white font-medium rounded-xl transition-all duration-300 hover:-translate-y-0.5"
                  >
                    Tech Blog
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
