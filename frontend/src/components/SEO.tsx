/**
 * SEO Component using React 19's native document metadata support.
 * 
 * React 19 automatically hoists <title>, <meta>, and <link> tags to <head>.
 * This provides a clean, type-safe way to manage SEO per page.
 */

interface SEOProps {
  title: string
  description: string
  canonical?: string
  type?: 'website' | 'article'
  image?: string
  imageAlt?: string
  publishedTime?: string
  modifiedTime?: string
  author?: string
  tags?: string[]
  noindex?: boolean
}

const SITE_NAME = 'Joseph Prince | CTO & Software Engineer at Sports Thread'
const BASE_URL = 'https://www.thejosephprince.com'
const DEFAULT_IMAGE = `${BASE_URL}/og-image.png`

export default function SEO({
  title,
  description,
  canonical,
  type = 'website',
  image = DEFAULT_IMAGE,
  imageAlt,
  publishedTime,
  modifiedTime,
  author = 'Joseph Prince',
  tags = [],
  noindex = false,
}: SEOProps) {
  const fullTitle = title === 'Home' 
    ? SITE_NAME 
    : `${title} | Joseph Prince`
  
  const canonicalUrl = canonical || (typeof window !== 'undefined' ? window.location.href : '')

  return (
    <>
      {/* Primary Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="title" content={fullTitle} />
      <meta name="description" content={description} />
      <meta name="author" content={author} />
      
      {/* Robots */}
      {noindex ? (
        <meta name="robots" content="noindex, nofollow" />
      ) : (
        <meta name="robots" content="index, follow" />
      )}
      
      {/* Canonical URL */}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta property="og:image:alt" content={imageAlt || title} />
      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:locale" content="en_US" />
      
      {/* Article-specific Open Graph */}
      {type === 'article' && publishedTime && (
        <meta property="article:published_time" content={publishedTime} />
      )}
      {type === 'article' && modifiedTime && (
        <meta property="article:modified_time" content={modifiedTime} />
      )}
      {type === 'article' && author && (
        <meta property="article:author" content={author} />
      )}
      {type === 'article' && tags.map((tag) => (
        <meta key={tag} property="article:tag" content={tag} />
      ))}
      
      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={canonicalUrl} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
      <meta name="twitter:image:alt" content={imageAlt || title} />
      
      {/* Keywords from tags */}
      {tags.length > 0 && (
        <meta name="keywords" content={tags.join(', ')} />
      )}
    </>
  )
}

/**
 * JSON-LD Structured Data Component
 * For rich search results (Google rich snippets)
 */
interface JsonLdProps {
  data: object
}

export function JsonLd({ data }: JsonLdProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

/**
 * Helper functions to generate structured data
 */
export function generatePersonSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    '@id': `${BASE_URL}/#person`,
    name: 'Joseph Prince',
    givenName: 'Joseph',
    familyName: 'Prince',
    alternateName: ['J Prince', 'Joseph Prince CTO', 'Joseph Prince Software Engineer'],
    disambiguatingDescription: 'Chief Technology Officer and Full Stack Software Engineer at Sports Thread, specializing in Python, TypeScript, React, and Django. Not to be confused with the Singaporean pastor.',
    jobTitle: 'Chief Technology Officer',
    description: 'CTO and Full Stack Engineer building scalable systems with Python, TypeScript, React, and Django. Leading engineering at Sports Thread serving 2M+ users.',
    worksFor: {
      '@type': 'Organization',
      name: 'Sports Thread',
      url: 'https://info.sportsthread.com',
      description: 'Sports event management platform providing age verification, registration, scheduling, ticketing, and athlete recruiting for 1000+ events and 2M+ users',
    },
    alumniOf: {
      '@type': 'CollegeOrUniversity',
      name: 'Colorado Technical University',
    },
    url: BASE_URL,
    sameAs: [
      'https://www.linkedin.com/in/thejprince/',
      'https://github.com/DedRozs',
    ],
    knowsAbout: [
      'Python',
      'TypeScript',
      'JavaScript',
      'React',
      'Django',
      'Clean Architecture',
      'Domain-Driven Design',
      'API Design',
      'Team Leadership',
      'Software Engineering',
      'Full Stack Development',
      'PostgreSQL',
      'Redis',
      'AWS',
      'Docker',
      'Kubernetes',
    ],
    hasOccupation: {
      '@type': 'Occupation',
      name: 'Software Engineer',
      occupationLocation: {
        '@type': 'Country',
        name: 'United States',
      },
      skills: 'Python, TypeScript, React, Django, Clean Architecture, API Design',
    },
  }
}

export function generateWebsiteSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': `${BASE_URL}/#website`,
    name: SITE_NAME,
    url: BASE_URL,
    description: 'Personal portfolio and technical blog of Joseph Prince, CTO and Full Stack Software Engineer at Sports Thread.',
    author: {
      '@id': `${BASE_URL}/#person`,
    },
    publisher: {
      '@id': `${BASE_URL}/#person`,
    },
    inLanguage: 'en-US',
    potentialAction: {
      '@type': 'SearchAction',
      target: `${BASE_URL}/blog?search={search_term_string}`,
      'query-input': 'required name=search_term_string',
    },
  }
}

export function generateProfessionalServiceSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'ProfessionalService',
    '@id': `${BASE_URL}/#service`,
    name: 'Joseph Prince - Software Engineering & Technical Leadership',
    description: 'Technical consulting, software architecture, and engineering leadership services by Joseph Prince, CTO at Sports Thread.',
    provider: {
      '@id': `${BASE_URL}/#person`,
    },
    areaServed: 'Worldwide',
    serviceType: ['Software Development', 'Technical Consulting', 'Engineering Leadership'],
    url: BASE_URL,
  }
}

export function generateBlogPostSchema(post: {
  title: string
  description: string
  slug: string
  publishedAt: string
  modifiedAt?: string
  tags?: string[]
  readingTime?: number
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.description,
    url: `${BASE_URL}/blog/${post.slug}`,
    datePublished: post.publishedAt,
    dateModified: post.modifiedAt || post.publishedAt,
    author: generatePersonSchema(),
    publisher: {
      '@type': 'Person',
      name: 'Joseph Prince',
      url: BASE_URL,
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${BASE_URL}/blog/${post.slug}`,
    },
    keywords: post.tags?.join(', '),
    timeRequired: post.readingTime ? `PT${post.readingTime}M` : undefined,
  }
}

export function generateBreadcrumbSchema(items: { name: string; url: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : `${BASE_URL}${item.url}`,
    })),
  }
}

/**
 * FAQ Schema - helps with disambiguation and rich snippets
 */
export function generateFAQSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: 'Who is Joseph Prince the software engineer?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Joseph Prince is a Chief Technology Officer (CTO) and Full Stack Software Engineer at Sports Thread, a sports event management platform providing age verification, registration, scheduling, ticketing, and athlete recruiting for 2M+ users. He specializes in Python, TypeScript, React, Django, Clean Architecture, and Domain-Driven Design. He is not related to the Singaporean pastor of the same name.',
        },
      },
      {
        '@type': 'Question',
        name: 'What technologies does Joseph Prince work with?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Joseph Prince specializes in Python, TypeScript, React, Django, PostgreSQL, Redis, AWS, Docker, and Kubernetes. He focuses on Clean Architecture and Domain-Driven Design patterns for building scalable systems.',
        },
      },
      {
        '@type': 'Question',
        name: 'Where does Joseph Prince work?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Joseph Prince is the CTO at Sports Thread, a sports event management platform where he leads engineering for age verification, registration, scheduling, ticketing, and athlete recruiting systems serving 2M+ users. He progressed from Marketing Manager to CTO in just 4 years.',
        },
      },
      {
        '@type': 'Question',
        name: 'Is this the same Joseph Prince as the pastor?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'No, this is Joseph Prince the software engineer and CTO, not the Singaporean pastor and televangelist. This Joseph Prince is a technology professional specializing in full stack development and engineering leadership.',
        },
      },
    ],
  }
}

/**
 * ProfilePage schema for About page - helps Google understand this is a profile
 */
export function generateProfilePageSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    '@id': `${BASE_URL}/about`,
    name: 'About Joseph Prince - CTO & Software Engineer',
    description: 'Professional profile of Joseph Prince, CTO at Sports Thread and Full Stack Software Engineer.',
    mainEntity: {
      '@id': `${BASE_URL}/#person`,
    },
    breadcrumb: {
      '@id': `${BASE_URL}/about#breadcrumb`,
    },
  }
}
