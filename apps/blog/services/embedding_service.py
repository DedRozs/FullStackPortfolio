import logging

import psycopg2
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 1536
DEFAULT_TOP_K = 5


class PostEmbeddingService:
    """
    Manages post embeddings stored in Supabase (pgvector).

    Post content lives in MySQL via the Post model. Only the vector
    representations are stored here, keyed by post_id. This keeps the
    primary database lean and lets vector similarity search scale
    independently via pgvector's IVFFlat index.
    """

    def __init__(self) -> None:
        self._openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _connect(self):
        return psycopg2.connect(settings.SUPABASE_DB_URL, sslmode='require')

    def _embed(self, text: str) -> list[float]:
        response = self._openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    def upsert(self, post_id: int, text: str) -> None:
        """Generate and store (or replace) the embedding for a post."""
        embedding = self._embed(text)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO post_embeddings (post_id, embedding)
                VALUES (%s, %s::vector)
                ON CONFLICT (post_id)
                DO UPDATE SET embedding = EXCLUDED.embedding,
                              updated_at = now()
                """,
                (post_id, str(embedding)),
            )

    def delete(self, post_id: int) -> None:
        """Remove the embedding for an unpublished or deleted post."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                'DELETE FROM post_embeddings WHERE post_id = %s',
                (post_id,),
            )

    def find_similar_post_ids(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[int]:
        """Return IDs of the posts most semantically similar to query."""
        embedding = self._embed(query)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT post_id
                FROM post_embeddings
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (str(embedding), top_k),
            )
            return [row[0] for row in cur.fetchall()]
