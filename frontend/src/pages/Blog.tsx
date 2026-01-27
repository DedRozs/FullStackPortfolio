import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  tags: string[]
  published_at: string
  read_time: number
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
  
  const currentPage = parseInt(searchParams.get('page') || '1')
  const currentTag = searchParams.get('tag') || ''

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true)
      try {
        let url = `/api/blog/posts/?page=${currentPage}`
        if (currentTag) {
          url += `&tag=${encodeURIComponent(currentTag)}`
        }
        
        const response = await fetch(url)
        if (response.ok) {
          const data: BlogResponse = await response.json()
          setPosts(data.posts)
          setTotalPages(data.total_pages)
        }
      } catch (error) {
        console.error('Error fetching posts:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPosts()
  }, [currentPage, currentTag])

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const response = await fetch('/api/blog/tags/')
        if (response.ok) {
          const data = await response.json()
          setTags(data.tags)
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

  const handlePageChange = (page: number) => {
    searchParams.set('page', page.toString())
    setSearchParams(searchParams)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <section className="py-16">
      <div className="max-w-6xl mx-auto px-6">
        <header className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Blog
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl">
            Thoughts on engineering, leadership, and building things that matter.
          </p>
        </header>

        {/* Tags Filter */}
        {tags.length > 0 && (
          <div className="mb-10">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleTagClick('')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  !currentTag
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
                }`}
              >
                All Posts
              </button>
              {tags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleTagClick(tag)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    currentTag === tag
                      ? 'bg-blue-600 text-white'
                      : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Posts Grid */}
        {loading ? (
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-dark-800 rounded-xl p-6 animate-pulse"
              >
                <div className="h-6 bg-dark-700 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-dark-700 rounded w-full mb-2"></div>
                <div className="h-4 bg-dark-700 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">
              {currentTag
                ? `No posts found with tag "${currentTag}"`
                : 'No blog posts yet. Check back soon!'}
            </p>
          </div>
        ) : (
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {posts.map((post) => (
              <article
                key={post.id}
                className="bg-dark-800 rounded-xl p-6 hover:bg-dark-700 transition group"
              >
                <Link to={`/blog/${post.slug}`}>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {post.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-dark-600 text-blue-400 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <h2 className="text-xl font-semibold text-white mb-3 group-hover:text-blue-400 transition">
                    {post.title}
                  </h2>
                  <p className="text-gray-400 mb-4 line-clamp-3">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
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

        {/* Pagination */}
        {totalPages > 1 && (
          <nav className="mt-12 flex justify-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Previous
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                className={`px-4 py-2 rounded-lg transition ${
                  page === currentPage
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Next
            </button>
          </nav>
        )}
      </div>
    </section>
  )
}
