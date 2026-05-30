import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Card, CardBody, CardHeader, CardTitle } from '../components/catalyst-ui-kit/typescript/card'

interface Tag {
  id: number
  name: string
  slug: string
}

interface RelatedPost {
  id: number
  title: string
  slug: string
  excerpt: string
  reading_time_minutes: number
  published_at: string
  author_display_name: string
  featured_image_url: string | null
  tags: Tag[]
}

interface PostDetail {
  id: number
  title: string
  slug: string
  excerpt: string
  body: string
  reading_time_minutes: number
  published_at: string
  author_display_name: string
  featured_image_url: string | null
  tags: Tag[]
  related_posts: RelatedPost[]
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<PostDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    setError(null)
    fetch(`/api/blog/posts/${slug}/`)
      .then((res) => {
        if (res.status === 404) {
          navigate('/blog', { replace: true })
          throw new Error('not-found')
        }
        if (!res.ok) throw new Error('Failed to load post.')
        return res.json() as Promise<PostDetail>
      })
      .then(setPost)
      .catch((err: Error) => {
        if (err.message !== 'not-found') setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [slug, navigate])

  if (loading) {
    return (
      <div className="flex justify-center py-40">
        <span className="text-text-muted font-display tracking-widest text-sm uppercase animate-pulse">
          Loading...
        </span>
      </div>
    )
  }

  if (error || !post) {
    return (
      <div className="flex justify-center py-40">
        <span className="text-neon-magenta font-display tracking-widest text-sm uppercase">
          {error ?? 'Post not found.'}
        </span>
      </div>
    )
  }

  return (
    <>
      {/* Hero */}
      <section className="scanlines relative pt-20 pb-10 px-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,27,114,0.4) 0%, transparent 70%)',
          }}
        />
        <div className="max-w-3xl mx-auto">
          <Link
            to="/blog"
            className="text-neon-cyan text-xs font-display tracking-widest uppercase hover:glow-cyan mb-8 inline-block transition-all"
          >
            &larr; Back to Blog
          </Link>

          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {post.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="px-2 py-0.5 text-[10px] font-display tracking-widest uppercase border border-neon-cyan/30 text-neon-cyan/70 rounded"
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}

          <h1 className="font-display text-3xl sm:text-4xl font-bold text-text-primary tracking-wide mb-4 animate-fade-in-up">
            {post.title}
          </h1>
          <p className="text-text-muted text-sm mb-6">
            {formatDate(post.published_at)} &middot; {post.reading_time_minutes} min read &middot;{' '}
            {post.author_display_name}
          </p>

          {post.featured_image_url && (
            <img
              src={post.featured_image_url}
              alt={post.title}
              className="w-full rounded border border-cyber-border mb-8 object-cover max-h-80"
            />
          )}
        </div>
      </section>

      {/* Body */}
      <section className="relative pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="blog-post-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.body}</ReactMarkdown>
          </div>

          {/* Related posts */}
          {post.related_posts.length > 0 && (
            <aside className="mt-16 pt-10 border-t border-cyber-border">
              <h2 className="font-display text-xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6">
                Related Posts
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {post.related_posts.map((related) => (
                  <Card key={related.id} flush accent="cyan">
                    <CardHeader>
                      <CardTitle>
                        <Link
                          to={`/blog/${related.slug}`}
                          className="hover:text-neon-cyan transition-colors text-sm"
                        >
                          {related.title}
                        </Link>
                      </CardTitle>
                      <p className="text-text-muted text-xs mt-1">
                        {formatDate(related.published_at)} &middot;{' '}
                        {related.reading_time_minutes} min read
                      </p>
                    </CardHeader>
                    <CardBody>
                      <p className="text-text-muted text-sm leading-relaxed line-clamp-3">
                        {related.excerpt}
                      </p>
                    </CardBody>
                  </Card>
                ))}
              </div>
            </aside>
          )}
        </div>
      </section>
    </>
  )
}
