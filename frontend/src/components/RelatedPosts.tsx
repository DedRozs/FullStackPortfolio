import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

interface RelatedPost {
  id: string
  title: string
  slug: string
  excerpt: string
  tags: string[]
  published_at: string
  reading_time: number
}

interface RelatedPostsProps {
  currentSlug: string
  currentTags: string[]
}

/**
 * Related Posts component for internal linking.
 * 
 * Internal linking is a critical SEO factor:
 * - Helps search engines discover and index content
 * - Distributes page authority throughout the site
 * - Increases user engagement and time-on-site
 * - Reduces bounce rate
 */
export default function RelatedPosts({ currentSlug, currentTags }: RelatedPostsProps) {
  const [relatedPosts, setRelatedPosts] = useState<RelatedPost[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRelatedPosts = async () => {
      try {
        // Fetch all published posts
        const response = await fetch('/api/blog/posts/')
        if (!response.ok) return
        
        const data = await response.json()
        const posts: RelatedPost[] = data.posts || []
        
        // Filter out current post and score by tag overlap
        const scoredPosts = posts
          .filter(post => post.slug !== currentSlug)
          .map(post => {
            // Calculate relevance score based on shared tags
            const sharedTags = post.tags.filter(tag => 
              currentTags.some(currentTag => 
                currentTag.toLowerCase() === tag.toLowerCase()
              )
            )
            return { post, score: sharedTags.length }
          })
          .sort((a, b) => b.score - a.score)
          .slice(0, 3)  // Top 3 related posts
          .map(({ post }) => post)
        
        setRelatedPosts(scoredPosts)
      } catch (error) {
        console.error('Error fetching related posts:', error)
      } finally {
        setLoading(false)
      }
    }

    if (currentTags.length > 0) {
      fetchRelatedPosts()
    } else {
      setLoading(false)
    }
  }, [currentSlug, currentTags])

  // Tag color variants
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  // Don't render if no related posts
  if (loading) {
    return (
      <section className="py-16 border-t border-gray-800">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-white mb-8">Related Articles</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-dark-800/50 border border-gray-800 rounded-xl p-5 animate-pulse">
                <div className="h-4 bg-dark-700 rounded w-3/4 mb-3" />
                <div className="h-4 bg-dark-700 rounded w-1/2 mb-4" />
                <div className="h-3 bg-dark-700 rounded w-1/4" />
              </div>
            ))}
          </div>
        </div>
      </section>
    )
  }

  if (relatedPosts.length === 0) {
    return null
  }

  return (
    <section className="py-16 border-t border-gray-800">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
          <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Related Articles
        </h2>
        
        <div className="grid gap-6 md:grid-cols-3">
          {relatedPosts.map(post => (
            <Link
              key={post.id}
              to={`/blog/${post.slug}`}
              className="group relative bg-dark-800/50 hover:bg-dark-800 border border-gray-800 hover:border-gray-700 rounded-xl p-5 transition-all duration-300 hover:-translate-y-1"
            >
              {/* Gradient accent on hover */}
              <div className="absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              {/* Tags */}
              <div className="flex flex-wrap gap-2 mb-3">
                {post.tags.slice(0, 2).map(tag => (
                  <span
                    key={tag}
                    className={`text-xs px-2 py-0.5 rounded-full bg-gradient-to-r ${getTagGradient(tag)} bg-opacity-10 text-gray-300`}
                    style={{ 
                      background: `linear-gradient(to right, rgb(59 130 246 / 0.15), rgb(6 182 212 / 0.15))` 
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
              
              {/* Title */}
              <h3 className="text-white font-semibold mb-2 line-clamp-2 group-hover:text-blue-400 transition-colors">
                {post.title}
              </h3>
              
              {/* Meta */}
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span>{formatDate(post.published_at)}</span>
                <span>·</span>
                <span>{post.reading_time} min read</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}
