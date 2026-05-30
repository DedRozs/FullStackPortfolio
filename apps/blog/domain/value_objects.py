from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Slug:
    value: str

    _PATTERN: re.Pattern = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        object.__setattr__(self, 'value', normalized)
        if not normalized:
            raise ValueError('Slug.value must not be empty.')
        if len(normalized) > 255:
            raise ValueError('Slug.value must not exceed 255 characters.')
        if not self._PATTERN.match(normalized):
            raise ValueError(
                f'Slug.value must match ^[a-z0-9]+(-[a-z0-9]+)*$, got: {normalized!r}'
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Excerpt:
    text: str

    _HTML_TAG: re.Pattern = re.compile(r'<[^>]+>')

    def __post_init__(self) -> None:
        cleaned = self._HTML_TAG.sub('', self.text).strip()
        object.__setattr__(self, 'text', cleaned)
        if not cleaned:
            raise ValueError('Excerpt.text must not be empty.')
        if len(cleaned) > 500:
            raise ValueError('Excerpt.text must not exceed 500 characters.')

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class ReadingTime:
    minutes: int

    def __post_init__(self) -> None:
        if not isinstance(self.minutes, int) or self.minutes < 1:
            raise ValueError('ReadingTime.minutes must be an integer >= 1.')

    def __str__(self) -> str:
        return f'{self.minutes} min read'


@dataclass(frozen=True)
class EmbeddingVector:
    values: tuple
    dimensions: int

    def __post_init__(self) -> None:
        converted = tuple(self.values)
        object.__setattr__(self, 'values', converted)
        if self.dimensions != 1536:
            raise ValueError('EmbeddingVector.dimensions must be 1536.')
        if len(converted) != self.dimensions:
            raise ValueError(
                f'EmbeddingVector length {len(converted)} does not match dimensions {self.dimensions}.'
            )
        for v in converted:
            if not math.isfinite(v):
                raise ValueError('EmbeddingVector contains non-finite float values.')


class PostStatus(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'


@dataclass(frozen=True)
class FeaturedImagePath:
    path: str

    def __post_init__(self) -> None:
        stripped = self.path.strip()
        object.__setattr__(self, 'path', stripped)
        if not stripped:
            raise ValueError('FeaturedImagePath.path must not be empty.')
        if stripped.startswith('/'):
            raise ValueError('FeaturedImagePath.path must not start with /.')
        if '..' in stripped:
            raise ValueError('FeaturedImagePath.path must not contain "..".')

    def __str__(self) -> str:
        return self.path
