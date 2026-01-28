"""Idea generation service using AI and trends data."""
import logging
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from django.conf import settings

from apps.blog.domain.entities import BlogIdea, IdeaStatus

logger = logging.getLogger(__name__)


@dataclass
class ExpertiseArea:
    """Defines an area of expertise for content generation."""
    name: str
    keywords: List[str]
    description: str


# Define your expertise areas
EXPERTISE_AREAS = [
    ExpertiseArea(
        name="AI & Machine Learning",
        keywords=["ai", "machine learning", "llm", "gpt", "neural", "openai", "anthropic", "ml"],
        description="Practical applications of AI/ML in software development"
    ),
    ExpertiseArea(
        name="Full-Stack Development",
        keywords=["python", "django", "react", "typescript", "javascript", "frontend", "backend", "api"],
        description="Modern full-stack web development practices"
    ),
    ExpertiseArea(
        name="Cloud Architecture",
        keywords=["cloud", "aws", "gcp", "azure", "kubernetes", "docker", "serverless", "devops"],
        description="Cloud infrastructure and DevOps practices"
    ),
    ExpertiseArea(
        name="Software Engineering",
        keywords=["engineering", "architecture", "testing", "code", "design", "agile", "startup"],
        description="Software engineering principles and practices"
    ),
    ExpertiseArea(
        name="Career & Tech Industry",
        keywords=["career", "hiring", "interview", "layoff", "remote", "engineer", "developer", "salary"],
        description="Career advice and tech industry insights"
    ),
]

# Tech RSS feeds - curated sources for trending topics
TECH_RSS_FEEDS = [
    # Software Engineering & Architecture
    {"url": "https://martinfowler.com/feed.atom", "source": "Martin Fowler", "area": "Software Engineering"},
    {"url": "https://blog.pragmaticengineer.com/rss/", "source": "Pragmatic Engineer", "area": "Software Engineering"},
    {"url": "https://www.infoq.com/feed/", "source": "InfoQ", "area": "Software Engineering"},
    
    # AI & Machine Learning
    {"url": "https://openai.com/blog/rss/", "source": "OpenAI Blog", "area": "AI & Machine Learning"},
    {"url": "https://www.deepmind.com/blog/rss.xml", "source": "DeepMind", "area": "AI & Machine Learning"},
    
    # Cloud & DevOps
    {"url": "https://aws.amazon.com/blogs/aws/feed/", "source": "AWS Blog", "area": "Cloud Architecture"},
    {"url": "https://cloud.google.com/blog/rss", "source": "Google Cloud Blog", "area": "Cloud Architecture"},
    
    # Tech Industry & Career
    {"url": "https://techcrunch.com/feed/", "source": "TechCrunch", "area": "Career & Tech Industry"},
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge", "area": "Career & Tech Industry"},
    
    # Full-Stack Development
    {"url": "https://dev.to/feed/", "source": "Dev.to", "area": "Full-Stack Development"},
    {"url": "https://css-tricks.com/feed/", "source": "CSS-Tricks", "area": "Full-Stack Development"},
]


class IdeaGeneratorService:
    """Service for generating blog post ideas using AI and trend data."""
    
    # Hacker News API endpoints (free, no auth required)
    HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
    HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
    
    def __init__(self, openai_api_key: str | None = None):
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self._client = None
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.openai_api_key)
        return self._client
    
    def get_rss_topics(self, expertise_areas: List[ExpertiseArea]) -> List[dict]:
        """Fetch recent articles from tech RSS feeds."""
        import feedparser
        
        target_areas = {area.name for area in expertise_areas}
        trending_topics = []
        
        for feed_info in TECH_RSS_FEEDS:
            if feed_info["area"] not in target_areas:
                continue
                
            try:
                feed = feedparser.parse(feed_info["url"])
                
                for entry in feed.entries[:5]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))[:200]
                    link = entry.get("link", "")
                    published = entry.get("published", entry.get("updated", ""))
                    
                    if title:
                        trending_topics.append({
                            "title": title,
                            "summary": summary,
                            "url": link,
                            "source": feed_info["source"],
                            "expertise_area": feed_info["area"],
                            "published": published,
                            "type": "rss"
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to fetch RSS from {feed_info['source']}: {e}")
                continue
        
        logger.info(f"Fetched {len(trending_topics)} articles from RSS feeds")
        return trending_topics

    def get_trending_topics(self, expertise_areas: List[ExpertiseArea]) -> List[dict]:
        """Fetch trending topics from Hacker News."""
        try:
            response = requests.get(self.HN_TOP_STORIES_URL, timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:100]
            
            all_keywords = set()
            keyword_to_area = {}
            for area in expertise_areas:
                for kw in area.keywords:
                    all_keywords.add(kw.lower())
                    keyword_to_area[kw.lower()] = area.name
            
            trending_topics = []
            stories_checked = 0
            
            for story_id in story_ids:
                if len(trending_topics) >= 15 or stories_checked >= 50:
                    break
                    
                try:
                    item_response = requests.get(
                        self.HN_ITEM_URL.format(story_id), 
                        timeout=5
                    )
                    item_response.raise_for_status()
                    story = item_response.json()
                    
                    if not story or story.get('type') != 'story':
                        continue
                    
                    title = story.get('title', '').lower()
                    url = story.get('url', '').lower()
                    score = story.get('score', 0)
                    stories_checked += 1
                    
                    for keyword in all_keywords:
                        if keyword in title or keyword in url:
                            trending_topics.append({
                                'title': story.get('title'),
                                'url': story.get('url', ''),
                                'score': score,
                                'comments': story.get('descendants', 0),
                                'matched_keyword': keyword,
                                'expertise_area': keyword_to_area.get(keyword, 'General')
                            })
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to fetch story {story_id}: {e}")
                    continue
            
            trending_topics.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"Found {len(trending_topics)} relevant HN stories from {stories_checked} checked")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Failed to fetch HN trends: {e}")
            return []
    
    def _build_idea_prompt(
        self,
        num_ideas: int,
        expertise_context: str,
        trends_context: str,
        existing_context: str
    ) -> str:
        """Build the prompt for idea generation."""
        prompt_parts = [
            "You are a content strategist for a senior software engineer's thought leadership blog.",
            "",
            "This is NOT a tutorial blog. We publish opinion pieces, industry analysis, and career insights.",
            "",
            "Areas of expertise:",
            expertise_context,
            "",
            trends_context,
            existing_context,
            "",
            f"Generate {num_ideas} unique blog post ideas. Each idea MUST be:",
            "1. THOUGHT LEADERSHIP - opinions, analysis, perspectives (NOT tutorials or how-to guides)",
            "2. OPINION-DRIVEN - takes a stance or shares a unique perspective",
            "3. NO IMPLEMENTATION - conceptual discussion, not coding advice",
            "4. ENGAGING - provocative, insightful, or challenges conventional thinking",
            "",
            "Good topic examples:",
            '- "Why Most Microservices Migrations Fail (And What Teams Get Wrong)"',
            '- "The Hidden Cost of Chasing Every New JavaScript Framework"',
            '- "What 5 Years of Code Reviews Taught Me About Engineering Culture"',
            '- "The Case Against Premature Optimization in Startup Engineering"',
            "",
            "BAD topic examples (DO NOT generate these):",
            '- "How to Build a REST API with Django" (tutorial)',
            '- "Getting Started with Kubernetes" (how-to guide)',
            '- "10 Python Tips for Beginners" (tips listicle)',
            '- "Building a Full-Stack App with React" (implementation guide)',
            "",
            "For each idea, provide:",
            "- topic: A compelling, opinion-driven blog post title (NOT a how-to title)",
            "- keywords: 3-5 relevant SEO keywords",
            "- expertise_area: Which area this falls under",
            "- brief: 1-2 sentence description of the PERSPECTIVE or ARGUMENT the post will make",
            "",
            "Respond in JSON format:",
            '{',
            '    "ideas": [',
            '        {',
            '            "topic": "...",',
            '            "keywords": ["...", "..."],',
            '            "expertise_area": "...",',
            '            "brief": "..."',
            '        }',
            '    ]',
            '}',
        ]
        return "\n".join(prompt_parts)

    def generate_ideas(
        self,
        num_ideas: int = 3,
        expertise_areas: List[ExpertiseArea] | None = None,
        existing_topics: List[str] | None = None,
    ) -> List[BlogIdea]:
        """Generate blog post ideas using AI."""
        expertise_areas = expertise_areas or EXPERTISE_AREAS
        existing_topics = existing_topics or []
        
        # Gather trending topics from multiple sources
        hn_trends = self.get_trending_topics(expertise_areas)
        rss_topics = self.get_rss_topics(expertise_areas)
        
        # Build context from both sources
        trends_context = ""
        
        if hn_trends:
            hn_lines = ["Currently trending on Hacker News:"]
            for t in hn_trends[:8]:
                hn_lines.append(f"- \"{t['title']}\" ({t['score']} points, {t['comments']} comments)")
            trends_context += "\n".join(hn_lines) + "\n\n"
        
        if rss_topics:
            rss_lines = ["Recent articles from tech publications:"]
            for t in rss_topics[:12]:
                rss_lines.append(f"- \"{t['title']}\" ({t['source']}) - {t['expertise_area']}")
            trends_context += "\n".join(rss_lines)
        
        existing_context = ""
        if existing_topics:
            existing_lines = ["\n\nTopics already covered (avoid these):"]
            for topic in existing_topics[:20]:
                existing_lines.append(f"- {topic}")
            existing_context = "\n".join(existing_lines)
        
        expertise_lines = []
        for area in expertise_areas:
            expertise_lines.append(f"- {area.name}: {area.description}")
        expertise_context = "\n".join(expertise_lines)
        
        prompt = self._build_idea_prompt(
            num_ideas=num_ideas,
            expertise_context=expertise_context,
            trends_context=trends_context,
            existing_context=existing_context
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a technical content strategist. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            ideas = []
            for idea_data in result.get('ideas', []):
                idea = BlogIdea(
                    topic=idea_data['topic'],
                    keywords=idea_data.get('keywords', []),
                    expertise_area=idea_data.get('expertise_area', 'General'),
                    source='ai_suggested',
                    trend_score=None,
                )
                ideas.append(idea)
            
            logger.info(f"Generated {len(ideas)} blog ideas")
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to generate ideas: {e}")
            return []
    
    def check_duplicate(self, topic: str, existing_topics: List[str], threshold: float = 0.8) -> bool:
        """Check if a topic is too similar to existing ones."""
        topic_words = set(topic.lower().split())
        
        for existing in existing_topics:
            existing_words = set(existing.lower().split())
            
            if not topic_words or not existing_words:
                continue
                
            intersection = len(topic_words & existing_words)
            union = len(topic_words | existing_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                return True
        
        return False
