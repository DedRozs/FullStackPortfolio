import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '../components/catalyst-ui-kit/typescript/badge'
import { Button } from '../components/catalyst-ui-kit/typescript/button'
import { Card, CardBody, CardFooter, CardHeader, CardTitle } from '../components/catalyst-ui-kit/typescript/card'
import { Heading } from '../components/catalyst-ui-kit/typescript/heading'
import { Text } from '../components/catalyst-ui-kit/typescript/text'

interface Tag {
  id: number
  name: string
  slug: string
}

interface PostListItem {
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

interface BlogListResponse {
  posts: PostListItem[]
  total: number
  page: number
  num_pages: number
  page_size: number
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function BlogPage() {
  const [data, setData] = useState<BlogListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const cardsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/blog/posts/?page=${page}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load posts.')
        return res.json() as Promise<BlogListResponse>
      })
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [page])

  useEffect(() => {
    if (!cardsRef.current || !data) return
    const cards = Array.from(cardsRef.current.querySelectorAll<HTMLElement>('.reveal'))
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target as HTMLElement
            el.style.transitionDelay = `${el.dataset.delay ?? 0}ms`
            el.classList.add('is-visible')
            observer.unobserve(el)
          }
        })
      },
      { threshold: 0.08 },
    )
    cards.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [data])

  return (
    <>
      {/* Hero */}
      <section className="scanlines relative pt-20 pb-10 flex flex-col items-center text-center px-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,27,114,0.4) 0%, transparent 70%)',
          }}
        />
        <Text
          className="text-neon-magenta text-xs font-display tracking-[0.4em] uppercase mb-3 animate-fade-in-up"
          style={{ animationDelay: '0s' }}
        >
          Thoughts &amp; Tutorials
        </Text>
        <Heading
          level={1}
          className="font-display text-4xl sm:text-5xl font-bold text-neon-cyan glow-cyan tracking-widest uppercase mb-6 animate-fade-in-up"
          style={{ animationDelay: '0.1s' }}
        >
          Blog
        </Heading>
        <Text
          className="text-lg max-w-2xl leading-relaxed animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          Articles on software architecture, Django, React, and the lessons learned
          building production systems.
        </Text>
      </section>

      {/* Post list */}
      <section className="relative pt-4 pb-16 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6">
          {loading && (
            <div className="flex justify-center py-20">
              <Text className="font-display tracking-widest text-sm uppercase animate-pulse">
                Loading...
              </Text>
            </div>
          )}

          {error && (
            <div className="flex justify-center py-20">
              <Text className="text-neon-magenta font-display tracking-widest text-sm uppercase">
                {error}
              </Text>
            </div>
          )}

          {!loading && !error && data?.posts.length === 0 && (
            <Text className="text-center py-20">No posts yet.</Text>
          )}

          {data && data.posts.length > 0 && (
            <>
              <div className="flex flex-col gap-6" ref={cardsRef}>
                {data.posts.map((post, i) => (
                  <Card
                    key={post.id}
                    flush
                    accent="cyan"
                    data-delay={i * 80}
                    className="reveal"
                  >
                    <CardHeader>
                      {post.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                          {post.tags.map((tag) => (
                            <Badge key={tag.id} color="neon-cyan" className="font-display text-[10px] tracking-widest uppercase">
                              {tag.name}
                            </Badge>
                          ))}
                        </div>
                      )}
                      <CardTitle>
                        <Link
                          to={`/blog/${post.slug}`}
                          className="hover:text-neon-cyan transition-colors"
                        >
                          {post.title}
                        </Link>
                      </CardTitle>
                      <Text className="text-xs mt-1">
                        {formatDate(post.published_at)} &middot;{' '}
                        {post.reading_time_minutes} min read &middot;{' '}
                        {post.author_display_name}
                      </Text>
                    </CardHeader>
                    <CardBody>
                      <Text className="leading-relaxed">{post.excerpt}</Text>
                    </CardBody>
                    <CardFooter>
                      <Link
                        to={`/blog/${post.slug}`}
                        className="text-neon-cyan text-sm font-display tracking-wider uppercase hover:glow-cyan transition-all"
                      >
                        Read more &rarr;
                      </Link>
                    </CardFooter>
                  </Card>
                ))}
              </div>

              {data.num_pages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-10">
                  <Button
                    color="neon-cyan-outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="font-display tracking-widest uppercase"
                  >
                    &larr; Prev
                  </Button>
                  <Text className="text-xs font-display tracking-wider">
                    {page} / {data.num_pages}
                  </Text>
                  <Button
                    color="neon-cyan-outline"
                    onClick={() => setPage((p) => Math.min(data.num_pages, p + 1))}
                    disabled={page === data.num_pages}
                    className="font-display tracking-widest uppercase"
                  >
                    Next &rarr;
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </>
  )
}
