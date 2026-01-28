"""AI prompts for trading post generation.

This module contains prompt builders for each trading post type:
- Pre-market analysis posts
- Post-market session recaps
- Weekly recap posts
"""
from apps.trading.application.content_generation.prompts.premarket_prompt import (
    PreMarketPromptBuilder,
    PreMarketContext,
    get_premarket_prompt_builder,
)
from apps.trading.application.content_generation.prompts.postmarket_prompt import (
    PostMarketPromptBuilder,
    PostMarketContext,
    get_postmarket_prompt_builder,
)
from apps.trading.application.content_generation.prompts.weekly_recap_prompt import (
    WeeklyRecapPromptBuilder,
    WeeklyRecapContext,
    get_weekly_recap_prompt_builder,
)

__all__ = [
    # Pre-market
    'PreMarketPromptBuilder',
    'PreMarketContext',
    'get_premarket_prompt_builder',
    # Post-market
    'PostMarketPromptBuilder',
    'PostMarketContext',
    'get_postmarket_prompt_builder',
    # Weekly recap
    'WeeklyRecapPromptBuilder',
    'WeeklyRecapContext',
    'get_weekly_recap_prompt_builder',
]
