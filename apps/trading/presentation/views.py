"""API views for the Trading bounded context."""
from dataclasses import dataclass
import json
from typing import List
from uuid import UUID

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.trading.application.commands import (
    CreateTradingPostCommand,
    UpdateTradingPostCommand,
    PublishTradingPostCommand,
    UnpublishTradingPostCommand,
    ArchiveTradingPostCommand,
    DeleteTradingPostCommand,
    ScheduleTradingPostCommand,
)
from apps.trading.application.queries import (
    GetTradingPostBySlugQuery,
    GetPublishedTradingPostsQuery,
    GetPostsByInstrumentQuery,
    GetPostsByTypeQuery,
    GetPostsByInstrumentAndTypeQuery,
    GetPostCountQuery,
    GetAllInstrumentsQuery,
    GetMarketSessionQuery,
    GetPriceLevelsQuery,
    GetTradingPostByIdQuery,
)
from apps.trading.application.services import (
    TradingApplicationService,
    get_trading_service,
)
from apps.trading.domain.entities import TradingPost, MarketSession, PriceLevel
from apps.trading.domain.value_objects import Instrument, PostType


# ---------------------
# DTOs for API responses
# ---------------------

@dataclass
class TradingPostDTO:
    """Data Transfer Object for TradingPost."""
    id: str
    instrument: str
    instrument_name: str
    post_type: str
    post_type_name: str
    title: str
    slug: str
    excerpt: str
    content: str
    session_date: str
    status: str
    reading_time: int
    created_at: str
    updated_at: str
    published_at: str | None
    scheduled_for: str | None
    meta_description: str | None
    price_levels: List[dict]
    
    @classmethod
    def from_entity(cls, entity: TradingPost) -> 'TradingPostDTO':
        """Create DTO from domain entity."""
        price_levels = [
            {
                'type': level.level_type.value,
                'type_name': level.level_type.display_name,
                'price': float(level.price.value),
            }
            for level in entity.price_levels
        ]
        
        return cls(
            id=str(entity.id),
            instrument=entity.instrument.short_name,
            instrument_name=entity.instrument.display_name,
            post_type=entity.post_type.value,
            post_type_name=entity.post_type.display_name,
            title=entity.title,
            slug=str(entity.slug),
            excerpt=entity.excerpt,
            content=entity.content,
            session_date=entity.session_date.isoformat(),
            status=entity.status.value,
            reading_time=entity.reading_time,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat(),
            published_at=entity.published_at.isoformat() if entity.published_at else None,
            scheduled_for=entity.scheduled_for.isoformat() if entity.scheduled_for else None,
            meta_description=entity.meta_description,
            price_levels=price_levels,
        )


@dataclass
class TradingPostSummaryDTO:
    """Lightweight DTO for post listings."""
    id: str
    instrument: str
    instrument_name: str
    post_type: str
    post_type_name: str
    title: str
    slug: str
    excerpt: str
    session_date: str
    reading_time: int
    published_at: str | None
    
    @classmethod
    def from_entity(cls, entity: TradingPost) -> 'TradingPostSummaryDTO':
        """Create summary DTO from domain entity."""
        return cls(
            id=str(entity.id),
            instrument=entity.instrument.short_name,
            instrument_name=entity.instrument.display_name,
            post_type=entity.post_type.value,
            post_type_name=entity.post_type.display_name,
            title=entity.title,
            slug=str(entity.slug),
            excerpt=entity.excerpt,
            session_date=entity.session_date.isoformat(),
            reading_time=entity.reading_time,
            published_at=entity.published_at.isoformat() if entity.published_at else None,
        )


@dataclass
class InstrumentDTO:
    """DTO for instrument information."""
    symbol: str
    short_name: str
    display_name: str
    
    @classmethod
    def from_instrument(cls, instrument: Instrument) -> 'InstrumentDTO':
        """Create DTO from Instrument value object."""
        return cls(
            symbol=instrument.value,
            short_name=instrument.short_name,
            display_name=instrument.display_name,
        )


# ---------------------
# Public API Views
# ---------------------

class TradingPostListView(View):
    """API endpoint for listing trading posts."""
    
    def get(self, request) -> JsonResponse:
        """Get published posts with pagination and optional filtering."""
        service = get_trading_service()
        
        # Parse query params
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('limit', 10))
        offset = (page - 1) * page_size
        instrument = request.GET.get('instrument')
        post_type = request.GET.get('type')
        
        # Handle filtering
        if instrument and post_type:
            query = GetPostsByInstrumentAndTypeQuery(
                instrument=instrument,
                post_type=post_type,
                limit=page_size,
                offset=offset,
            )
            posts = service.get_posts_by_instrument_and_type(query)
            count_query = GetPostCountQuery(instrument=instrument)
        elif instrument:
            query = GetPostsByInstrumentQuery(
                instrument=instrument,
                limit=page_size,
                offset=offset,
            )
            posts = service.get_posts_by_instrument(query)
            count_query = GetPostCountQuery(instrument=instrument)
        elif post_type:
            query = GetPostsByTypeQuery(
                post_type=post_type,
                limit=page_size,
                offset=offset,
            )
            posts = service.get_posts_by_type(query)
            count_query = GetPostCountQuery()
        else:
            query = GetPublishedTradingPostsQuery(limit=page_size, offset=offset)
            posts = service.get_published_posts(query)
            count_query = GetPostCountQuery()
        
        total = service.get_post_count(count_query)
        total_pages = max(1, (total + page_size - 1) // page_size)
        
        return JsonResponse({
            'posts': [TradingPostSummaryDTO.from_entity(p).__dict__ for p in posts],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })


class TradingPostDetailView(View):
    """API endpoint for a single trading post."""
    
    def get(self, request, slug: str) -> JsonResponse:
        """Get a single post by slug."""
        service = get_trading_service()
        query = GetTradingPostBySlugQuery(slug=slug)
        post = service.get_post_by_slug(query)
        
        if post is None:
            return JsonResponse({
                'error': 'Post not found',
            }, status=404)
        
        return JsonResponse({
            'post': TradingPostDTO.from_entity(post).__dict__,
        })


class InstrumentListView(View):
    """API endpoint for listing available instruments."""
    
    def get(self, request) -> JsonResponse:
        """Get all available instruments."""
        service = get_trading_service()
        query = GetAllInstrumentsQuery()
        instruments = service.get_all_instruments(query)
        
        return JsonResponse({
            'instruments': [InstrumentDTO.from_instrument(i).__dict__ for i in instruments],
        })


class InstrumentPostsView(View):
    """API endpoint for posts by instrument."""
    
    def get(self, request, instrument: str) -> JsonResponse:
        """Get posts for a specific instrument."""
        service = get_trading_service()
        
        # Parse query params
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('limit', 10))
        offset = (page - 1) * page_size
        post_type = request.GET.get('type')
        
        if post_type:
            query = GetPostsByInstrumentAndTypeQuery(
                instrument=instrument.upper(),
                post_type=post_type,
                limit=page_size,
                offset=offset,
            )
            posts = service.get_posts_by_instrument_and_type(query)
        else:
            query = GetPostsByInstrumentQuery(
                instrument=instrument.upper(),
                limit=page_size,
                offset=offset,
            )
            posts = service.get_posts_by_instrument(query)
        
        count_query = GetPostCountQuery(instrument=instrument.upper())
        total = service.get_post_count(count_query)
        total_pages = max(1, (total + page_size - 1) // page_size)
        
        return JsonResponse({
            'posts': [TradingPostSummaryDTO.from_entity(p).__dict__ for p in posts],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'instrument': instrument.upper(),
        })


class PostTypeListView(View):
    """API endpoint for listing available post types."""
    
    def get(self, request) -> JsonResponse:
        """Get all available post types."""
        post_types = [
            {
                'value': pt.value,
                'name': pt.display_name,
            }
            for pt in PostType
        ]
        
        return JsonResponse({
            'post_types': post_types,
        })


# ---------------------
# Admin API Views
# ---------------------

@method_decorator(csrf_exempt, name='dispatch')
class AdminTradingPostView(View):
    """Admin API for managing trading posts."""
    
    def post(self, request) -> JsonResponse:
        """Create a new trading post."""
        try:
            data = json.loads(request.body)
            
            from datetime import date as date_type
            session_date = date_type.fromisoformat(data.get('session_date'))
            
            command = CreateTradingPostCommand(
                instrument=Instrument.from_short_name(data.get('instrument')),
                post_type=PostType(data.get('post_type')),
                title=data.get('title', ''),
                content=data.get('content', ''),
                session_date=session_date,
                meta_description=data.get('meta_description'),
            )
            
            service = get_trading_service()
            post_id = service.create_post(command)
            
            return JsonResponse({
                'success': True,
                'post_id': str(post_id),
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminTradingPostDetailView(View):
    """Admin API for managing a specific trading post."""
    
    def get(self, request, post_id: str) -> JsonResponse:
        """Get a post by ID."""
        try:
            service = get_trading_service()
            query = GetTradingPostByIdQuery(post_id=UUID(post_id))
            post = service.get_post_by_id(query)
            
            if post is None:
                return JsonResponse({
                    'error': 'Post not found',
                }, status=404)
            
            return JsonResponse({
                'post': TradingPostDTO.from_entity(post).__dict__,
            })
            
        except ValueError:
            return JsonResponse({
                'error': 'Invalid post ID',
            }, status=400)
    
    def put(self, request, post_id: str) -> JsonResponse:
        """Update a trading post."""
        try:
            data = json.loads(request.body)
            
            command = UpdateTradingPostCommand(
                post_id=UUID(post_id),
                title=data.get('title', ''),
                content=data.get('content', ''),
                meta_description=data.get('meta_description'),
            )
            
            service = get_trading_service()
            service.update_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
            }, status=400)
    
    def delete(self, request, post_id: str) -> JsonResponse:
        """Delete a trading post."""
        try:
            command = DeleteTradingPostCommand(post_id=UUID(post_id))
            
            service = get_trading_service()
            service.delete_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminPublishPostView(View):
    """Admin API for publishing a trading post."""
    
    def post(self, request, post_id: str) -> JsonResponse:
        """Publish a trading post."""
        try:
            command = PublishTradingPostCommand(post_id=UUID(post_id))
            
            service = get_trading_service()
            service.publish_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminUnpublishPostView(View):
    """Admin API for unpublishing a trading post."""
    
    def post(self, request, post_id: str) -> JsonResponse:
        """Unpublish a trading post."""
        try:
            command = UnpublishTradingPostCommand(post_id=UUID(post_id))
            
            service = get_trading_service()
            service.unpublish_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminSchedulePostView(View):
    """Admin API for scheduling a trading post."""
    
    def post(self, request, post_id: str) -> JsonResponse:
        """Schedule a trading post for future publication."""
        try:
            data = json.loads(request.body)
            
            from datetime import datetime
            publish_at = datetime.fromisoformat(data.get('publish_at'))
            
            command = ScheduleTradingPostCommand(
                post_id=UUID(post_id),
                publish_at=publish_at,
            )
            
            service = get_trading_service()
            service.schedule_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminArchivePostView(View):
    """Admin API for archiving a trading post."""
    
    def post(self, request, post_id: str) -> JsonResponse:
        """Archive a trading post."""
        try:
            command = ArchiveTradingPostCommand(post_id=UUID(post_id))
            
            service = get_trading_service()
            service.archive_post(command)
            
            return JsonResponse({
                'success': True,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
