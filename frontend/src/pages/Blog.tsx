import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  tags: string[]
  published_at: string
  reading_time: number
}

interface BlogResponse {
  posts: BlogPost[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export default function Blog() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [totalPages, setTotalPages] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  
  const currentPage = parseInt(searchParams.get('page') || '1')
  const currentTag = searchParams.get('tag') || ''
  const currentSearch = searchParams.get('search') || ''

  // Sync search input with URL on mount
  useEffect(() => {
    setSearchInput(currentSearch)
  }, [currentSearch])

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true)
      try {
        let url = `/api/blog/posts/?page=${currentPage}`
        if (currentTag) {
          url += `&tag=${encodeURIComponent(currentTag)}`
        }
        if (currentSearch) {
          url += `&search=${encodeURIComponent(currentSearch)}`
        }
        
        const response = await fetch(url)
        if (response.ok) {
          const data: BlogResponse = await response.json()
          setPosts(data.posts || [])
          setTotalPages(data.total_pages || 1)
        }
      } catch (error) {
        console.error('Error fetching posts:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPosts()
  }, [currentPage, currentTag, currentSearch])

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const response = await fetch('/api/blog/tags/')
        if (response.ok) {
          const data = await response.json()
          setTags(data.tags || [])
        }
      } catch (error) {
        console.error('Error fetching tags:', error)
      }
    }

    fetchTags()
  }, [])

  const handleTagClick = (tag: string) => {
    if (tag === currentTag) {
      searchParams.delete('tag')
    } else {
      searchParams.set('tag', tag)
    }
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = searchInput.trim()
    if (trimmed) {
      searchParams.set('search', trimmed)
    } else {
      searchParams.delete('search')
    }
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }, [searchInput, searchParams, setSearchParams])

  const clearSearch = () => {
    setSearchInput('')
    searchParams.delete('search')
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }

  const clearAllFilters = () => {
    setSearchInput('')
    searchParams.delete('search')
    searchParams.delete('tag')
    searchParams.set('page', '1')
    setSearchParams(searchParams)
  }

  const handlePageChange = (page: number) => {
    searchParams.set('page', page.toString())
    setSearchParams(searchParams)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const hasActiveFilters = currentTag || currentSearch

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

  return (
    <>
      {/* Hero Section */}
      <section className="min-h-[50vh] flex items-center relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-full blur-3xl" />
        
        <div className="max-w-6xl mx-auto px-6 relative z-10 w-full">
          <div className="max-w-3xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-dark-800/80 border border-gray-700 rounded-full mb-8 backdrop-blur-sm">
              <span className="text-blue-400">📝</span>
              <span className="text-sm text-gray-300">Engineering Blog</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                Thoughts &
              </span>
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                Insights
              </span>
            </h1>
            <p className="text-lg md:text-xl text-gray-400 leading-relaxed max-w-2xl">
              Deep dives into engineering, leadership, architecture patterns, and lessons learned building scalable systems.
            </p>
          </div>
        </div>
      </section>

      {/* Posts Section */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          {/* Search and Filter Bar */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 mb-10">
            {/* Search Input */}
            <form onSubmit={handleSearch} className="flex-1 max-w-md">
              <div className="relative">
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search articles..."
                  className="w-full bg-dark-800 border border-gray-700 hover:border-gray-600 text-white pl-11 pr-4 py-3 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors placeholder:text-gray-500"
                />
                <div className="absolute inset-y-0 left-0 flex items-center pl-4">
                  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                {searchInput && (
                  <button
                    type="button"
                    onClick={clearSearch}
                    className="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-500 hover:text-white transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </form>
            
            {/* Filters */}
            <div className="flex items-center gap-3">
              {/* Tag filter dropdown */}
              {tags.length > 0 && (
                <div className="relative">
                  <select
                    value={currentTag}
                    onChange={(e) => handleTagClick(e.target.value)}
                    className="appearance-none bg-dark-800 border border-gray-700 hover:border-gray-600 text-gray-300 pl-4 pr-10 py-3 rounded-xl text-sm font-medium focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors cursor-pointer min-w-[140px]"
                  >
                    <option value="">All Topics</option>
                    {tags.map((tag) => (
                      <option key={tag} value={tag}>
                        {tag}
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                    <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              )}
              
              {/* Clear all filters */}
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
          </div>
          
          {/* Results Header */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-white">
              {currentSearch ? (
                <>Results for <span className="text-blue-400">"{currentSearch}"</span>{currentTag && <> in <span className="text-purple-400">{currentTag}</span></>}</>
              ) : currentTag ? (
                <>Posts tagged <span className="text-blue-400">"{currentTag}"</span></>
              ) : (
                'All Articles'
              )}
            </h2>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="group relative bg-dark-800/50 border border-gray-800 rounded-2xl p-6 animate-pulse"
                >
                  <div className="flex gap-2 mb-4">
                    <div className="h-6 w-16 bg-dark-700 rounded-full"></div>
                    <div className="h-6 w-20 bg-dark-700 rounded-full"></div>
                  </div>
                  <div className="h-7 bg-dark-700 rounded-lg w-4/5 mb-4"></div>
                  <div className="space-y-2 mb-6">
                    <div className="h-4 bg-dark-700 rounded w-full"></div>
                    <div className="h-4 bg-dark-700 rounded w-5/6"></div>
                    <div className="h-4 bg-dark-700 rounded w-3/4"></div>
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
                <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-xl" />
                <div className="relative w-20 h-20 rounded-full bg-dark-800 border border-gray-700 flex items-center justify-center mx-auto mb-6">
                  <span className="text-4xl">{currentSearch ? '🔍' : '📭'}</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">
                {currentSearch
                  ? `No results for "${currentSearch}"`
                  : currentTag
                    ? `No posts found with tag "${currentTag}"`
                    : 'No posts yet'}
              </h3>
              <p className="text-gray-400 mb-8 max-w-md mx-auto">
                {currentSearch
                  ? 'Try a different search term or browse all posts.'
                  : currentTag
                    ? 'Try selecting a different tag or browse all posts.'
                    : 'Check back soon for new articles on engineering and technology.'}
              </p>
              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
                >
                  View All Posts
                </button>
              )}
            </div>
          ) : (
            /* Posts Grid */
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {posts.map((post, index) => (
                <article
                  key={post.id}
                  className="group relative bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-2xl p-6 transition-all duration-500 hover:-translate-y-2"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Gradient accent on hover */}
                  <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  
                  <Link to={`/blog/${post.slug}`} className="block">
                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {post.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className={`px-3 py-1 text-xs font-medium rounded-full bg-gradient-to-r ${getTagGradient(tag)} text-white`}
                        >
                          {tag}
                        </span>
                      ))}
                      {post.tags.length > 2 && (
                        <span className="px-3 py-1 text-xs font-medium rounded-full bg-dark-700 text-gray-400">
                          +{post.tags.length - 2}
                        </span>
                      )}
                    </div>
                    
                    {/* Title */}
                    <h2 className="text-xl font-semibold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-purple-400 transition-all duration-300 line-clamp-2">
                      {post.title}
                    </h2>
                    
                    {/* Excerpt */}
                    <p className="text-gray-400 text-sm leading-relaxed mb-6 line-clamp-3">
                      {post.excerpt}
                    </p>
                    
                    {/* Meta info */}
                    <div className="flex items-center justify-between text-sm">
                      <time dateTime={post.published_at} className="text-gray-500">
                        {formatDate(post.published_at)}
                      </time>
                      <span className="flex items-center gap-1.5 text-gray-500">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {post.reading_time} min
                      </span>
                    </div>
                    
                    {/* Read more indicator */}
                    <div className="mt-6 pt-4 border-t border-gray-800 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-blue-400 text-sm font-medium">Read article</span>
                      <svg className="w-4 h-4 text-blue-400 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/25'
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
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
            <div className="relative bg-dark-800/90 border border-gray-800 rounded-2xl p-8 md:p-12">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Want to collaborate?</h3>
                  <p className="text-gray-400">I'm always open to discussing new projects and opportunities.</p>
                </div>
                <Link
                  to="/contact"
                  className="group/btn px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 whitespace-nowrap flex items-center gap-2"
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
      </section>
    </>
  )
}
