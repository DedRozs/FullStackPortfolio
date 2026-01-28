"""Content generation pipeline for trading blog posts.

This module implements AI-powered content generation for trading analysis:
- Pre-market analysis with key levels and overnight context
- Post-market recaps analyzing session price action
- Weekly recap posts summarizing the trading week

Multi-model pipeline:
- o3-mini (reasoning): Content generation
- gpt-5-mini (fast): Content review and validation
"""
from apps.trading.application.content_generation.trading_post_generator import (
    TradingPostGeneratorService,
    GenerationResult,
    GenerationLog,
    get_trading_post_generator,
)
from apps.trading.application.content_generation.reviewer import (
    TradingPostReviewerService,
    ReviewResult,
    ReviewLog,
    get_trading_post_reviewer,
)
from apps.trading.application.content_generation.pipeline import (
    TradingContentPipeline,
    PipelineResult,
    get_trading_content_pipeline,
)
from apps.trading.application.content_generation.prompts import (
    PreMarketPromptBuilder,
    PreMarketContext,
    PostMarketPromptBuilder,
    PostMarketContext,
    WeeklyRecapPromptBuilder,
    WeeklyRecapContext,
)

__all__ = [
    # Main generator (o3-mini)
    'TradingPostGeneratorService',
    'GenerationResult',
    'GenerationLog',
    'get_trading_post_generator',
    # Content reviewer (gpt-5-mini)
    'TradingPostReviewerService',
    'ReviewResult',
    'ReviewLog',
    'get_trading_post_reviewer',
    # Pipeline
    'TradingContentPipeline',
    'PipelineResult',
    'get_trading_content_pipeline',
    # Prompt builders
    'PreMarketPromptBuilder',
    'PreMarketContext',
    'PostMarketPromptBuilder',
    'PostMarketContext',
    'WeeklyRecapPromptBuilder',
    'WeeklyRecapContext',
]

