# Trading Blog Implementation Plan

## Overview

A futures-focused technical analysis blog providing daily pre-market levels and post-market recaps for index futures instruments. Content is AI-generated from market data stored locally (fetched from Databento).

| Aspect | Decision |
|--------|----------|
| Bounded Context | `apps/trading/` (separate from tech blog) |
| Data Source | **Databento** (GLBX.MDP3, 1-minute bars stored locally) |
| Data Storage | `IntradayBarModel` - all 1m bars stored in DB |
| Instruments | NQ, ES, RTY |
| Post Structure | One post per instrument |
| Content Cadence | Pre-market + Post-market daily, Weekly recap Saturday |
| Frontend Route | `/trading-blog/` |
| Content Generation | Separate AI prompts, shared pipeline architecture with tech blog |

---

## Data Architecture

### Data Flow (Databento → Local Storage → Content Generation)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY DATA PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FETCH (Daily, after market close)                          │
│     python manage.py fetch_intraday_bars                        │
│     └── Databento API → IntradayBarModel (1-minute bars)       │
│                                                                 │
│  2. VERIFY (Before generation)                                  │
│     python manage.py ensure_trading_data                        │
│     └── Checks RTH + overnight bars exist                      │
│                                                                 │
│  3. GENERATE (Uses local data only)                            │
│     python manage.py generate_trading_content                   │
│     └── LocalMarketDataService → computes OHLC from 1m bars    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Storage

| Model | Purpose | Update Strategy |
|-------|---------|-----------------|
| `IntradayBarModel` | 1-minute OHLCV bars | `bulk_create(ignore_conflicts)` - fetch once, keep forever |
| `MarketSessionModel` | Daily OHLC aggregates | `update_or_create` - computed from IntradayBarModel |
| `WeeklySessionModel` | Weekly aggregates | `update_or_create` - computed from daily sessions |
| `TradingPostModel` | Generated content | Skip if exists, use `--force` to regenerate |

### Cost Control

Databento charges per GB transmitted. To minimize costs:
1. **Fetch once**: Data is stored locally after first fetch
2. **Check before fetch**: `ensure_trading_data` verifies what's already stored
3. **No external API calls during generation**: Pipeline reads from local DB only

---

## Content Strategy

### Daily Content (Monday–Friday)

| Time (ET) | Posts Generated |
|-----------|-----------------|
| 9:00 AM | NQ Pre-Market, ES Pre-Market, RTY Pre-Market, YM Pre-Market |
| 4:30 PM | NQ Recap, ES Recap, RTY Recap, YM Recap |

### Weekend Content

| Day | Posts Generated |
|-----|-----------------|
| Saturday 10:00 AM | NQ Weekly Recap, ES Weekly Recap, RTY Weekly Recap, YM Weekly Recap |

### Monthly Volume

~184 posts (8/day × 22 trading days + 4/week × 4 weeks)

---

## Content Templates

### Pre-Market Post Structure

1. Headline: "{Instrument} Pre-Market Analysis – {Date}"
2. Overnight summary (what happened in Globex session)
3. Key levels table (prior day, overnight, weekly, monthly)
4. Weekly/monthly context
5. Zones to watch for the session
6. Disclaimer

### Post-Market Recap Structure

1. Headline: "{Instrument} Session Recap – {Date}"
2. Session summary (high/low/close, range, % change)
3. How pre-market levels played out (held/broke)
4. Notable price action observations
5. Setup context for next session
6. Disclaimer

### Weekly Recap Structure

1. Headline: "{Instrument} Weekly Recap – Week of {Date}"
2. Week performance (open, high, low, close, % change)
3. Daily breakdown summary
4. Key levels that mattered during the week
5. Looking ahead to next week
6. Disclaimer

---

## Price Levels Calculated

| Level | Source |
|-------|--------|
| Prior Day High | Previous session high |
| Prior Day Low | Previous session low |
| Prior Day Close | Previous session close |
| Overnight High | Globex session high (6 PM – 9:30 AM ET) |
| Overnight Low | Globex session low |
| Weekly Open | Monday's opening price |
| Weekly High | Running high for current week |
| Weekly Low | Running low for current week |
| Monthly High | Running high for current month |
| Monthly Low | Running low for current month |

---

## Domain Model

### Entities

| Entity | Purpose |
|--------|---------|
| MarketSession | One trading day's data for one instrument |
| PriceLevel | Individual S/R level with type and value |
| TradingPost | Generated blog content for one instrument/session |
| WeeklySession | Aggregated week data for recap posts |

### Value Objects

| Value Object | Values |
|--------------|--------|
| Instrument | NQ, ES, RTY, YM |
| PostType | PRE_MARKET, POST_MARKET, WEEKLY_RECAP |
| LevelType | PRIOR_HIGH, PRIOR_LOW, PRIOR_CLOSE, OVERNIGHT_HIGH, OVERNIGHT_LOW, WEEKLY_OPEN, WEEKLY_HIGH, WEEKLY_LOW, MONTHLY_HIGH, MONTHLY_LOW |

### Domain Events

| Event | Trigger |
|-------|---------|
| IntradayBarsFetched | Databento data stored in IntradayBarModel |
| PriceLevelsCalculated | Levels computed from session data |
| TradingPostGenerated | AI content created |
| TradingPostPublished | Post published to blog |

---

## Data Pipeline

### Pipeline Flow

**Automatic Data Fetching (Default)**
- Pipeline automatically fetches missing data from Databento before generation
- `MarketDataSyncService` checks local data, fetches only what's missing
- Cost-efficient: never re-fetches data already in database
- Single command to generate: `python manage.py generate_trading_content`

**Manual Data Management (Optional)**
1. **Data fetch** (daily, after market close ~4:30 PM ET)
   - `fetch_intraday_bars` pulls 1-minute bars from Databento
   - Stores in `IntradayBarModel` (skips existing data)
   
2. **Data verification** (before any generation)
   - `ensure_trading_data` checks required bars exist
   - Reports what data is missing with fetch commands

3. **Content generation** (scheduled times)
   - `LocalMarketDataService` computes session OHLC from stored bars
   - `IntradayAnalysisService` provides all 1-minute bars (~1,500 per session)
   - AI generates content using verified local data with full price action context
   - No external API calls during generation (unless auto-fetch enabled)

### CME Futures Session Schedule

| Session | Time (ET) | Duration | Bars |
|---------|-----------|----------|------|
| Overnight | 6:00 PM - 9:30 AM | 15.5 hrs | ~930 |
| Opening 30min | 9:30 AM - 10:00 AM | 30 min | ~30 |
| Mid-Session | 10:00 AM - 3:00 PM | 5 hrs | ~300 |
| Final Hour | 3:00 PM - 4:00 PM | 1 hr | ~60 |
| Post-Cash | 4:00 PM - 5:00 PM | 1 hr | ~60 |
| Maintenance | 5:00 PM - 6:00 PM | 1 hr | — |

**Total bars per session: ~1,380**

### AI Model Configuration

Different models optimized for each post type's context size and reasoning needs:

| Post Type | Model | Context | Data Size | Notes |
|-----------|-------|---------|-----------|-------|
| Post-Market | `o3` | 200K tokens | ~30K tokens | All RTH + overnight 1m bars |
| Pre-Market | `o3-mini` | 200K tokens | ~5K tokens | Prior day summary, key levels |
| Weekly Recap | `o3` | 200K tokens | ~150K tokens | 5 days × 1,440 bars |

**Environment Variables:**
```
TRADING_MODEL_POSTMARKET=o3
TRADING_MODEL_PREMARKET=o3-mini  
TRADING_MODEL_WEEKLY=o3
```

### Management Commands

| Command | Purpose |
|---------|---------|
| `fetch_intraday_bars` | Pull 1m bars from Databento → IntradayBarModel |
| `ensure_trading_data` | Verify data exists before generation |
| `generate_trading_content` | Generate posts (auto-fetches missing data) |

### Scheduling Matrix

| Job | Time (ET) | Days | Output |
|-----|-----------|------|--------|
| Generate Pre-Market Posts | 8:30 AM | Mon–Fri | 4 posts (publish at 9:00 AM) |
| Generate Post-Market Posts | 4:15 PM | Mon–Fri | 4 posts (publish at 4:30 PM) |
| Generate Weekly Recaps | 9:30 AM | Saturday | 4 posts (publish at 10:00 AM) |

---

## URL Structure

| URL | Description |
|-----|-------------|
| `/trading-blog/` | Latest posts, all instruments |
| `/trading-blog/nq/` | NQ posts only |
| `/trading-blog/es/` | ES posts only |
| `/trading-blog/rty/` | RTY posts only |
| `/trading-blog/ym/` | YM posts only |
| `/trading-blog/<slug>/` | Individual post detail |
| `/trading-blog/feed/` | RSS feed (all instruments) |
| `/trading-blog/<instrument>/feed/` | RSS feed (per instrument) |

---

## File Structure

```
apps/trading/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── market_session.py
│   │   ├── price_level.py
│   │   ├── trading_post.py
│   │   └── weekly_session.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── instrument.py
│   │   ├── post_type.py
│   │   └── level_type.py
│   ├── events.py
│   └── repositories.py
├── application/
│   ├── __init__.py
│   ├── services.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── fetch_market_data.py
│   │   ├── calculate_levels.py
│   │   └── generate_trading_post.py
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── get_latest_posts.py
│   │   └── get_posts_by_instrument.py
│   └── content_generation/
│       ├── __init__.py
│       ├── prompts/
│       │   ├── premarket_prompt.py
│       │   ├── postmarket_prompt.py
│       │   └── weekly_recap_prompt.py
│       └── trading_post_generator.py
├── infrastructure/
│   ├── __init__.py
│   ├── models.py
│   ├── repositories.py
│   └── market_data/
│       ├── __init__.py
│       └── yfinance_client.py
├── presentation/
│   ├── __init__.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── feeds.py
│   └── sitemaps.py
├── migrations/
│   └── __init__.py
└── management/
    └── commands/
        ├── __init__.py
        ├── generate_premarket_posts.py
        ├── generate_postmarket_posts.py
        └── generate_weekly_recaps.py
```

---

## Implementation Phases

### Phase 1: Domain Layer

- Define entities (MarketSession, PriceLevel, TradingPost, WeeklySession)
- Define value objects (Instrument, PostType, LevelType)
- Define domain events
- Define repository interfaces

### Phase 2: Infrastructure Layer

- Create Django ORM models
- Implement yfinance client for market data fetching
- Implement repository classes

### Phase 3: Application Layer

- Implement commands (fetch data, calculate levels, generate posts)
- Implement queries (get latest posts, get by instrument)
- Create application service to orchestrate the pipeline

### Phase 4: Content Generation

- Design AI prompts for pre-market posts
- Design AI prompts for post-market recaps
- Design AI prompts for weekly recaps
- Implement trading post generator service

### Phase 5: Presentation Layer

- Create API views
- Configure URL routing
- Set up admin interface
- Implement RSS feeds
- Create sitemaps

### Phase 6: Frontend (React)

- Create trading blog list page component
- Create instrument filter components
- Create trading post detail page component
- Configure React Router for `/trading-blog/` routes

### Phase 7: Scheduling

- Create Django management commands for each post type
- Configure cron jobs or task scheduler
- Add error handling and retry logic
- Set up monitoring/alerting for failed jobs

### Phase 8: Testing

- Unit tests for level calculations
- Unit tests for domain entities and value objects
- Integration tests for yfinance client
- Integration tests for full pipeline
- End-to-end tests for API endpoints

---

## Dependencies

### Python Packages (to add to requirements.txt)

- yfinance (market data)

### Existing Infrastructure (reused)

- OpenAI/AI service (from tech blog content generation)
- Event bus (from shared domain)
- Base repository patterns (from shared infrastructure)

---

## Affiliate Integration Notes

This blog directly supports the Take Profit Trader affiliate application by providing:

- **Established audience** → Organic traffic from traders searching for NQ/ES/RTY/YM analysis
- **Measurable engagement** → Page views, RSS subscribers, email signups
- **Active trader audience** → Content specifically targets futures traders
- **Marketing channels** → Blog URL to provide in affiliate application question 5
- **Promotional tactics** → Natural integration point for TPT affiliate links in content

---

## Open Considerations

- **Email capture**: Consider adding newsletter signup for trading insights
- **Social integration**: Auto-post to Twitter/X when new analysis published
- **Performance tracking**: Add analytics to track which instruments/post types perform best
- **User feedback**: Consider adding comments or feedback mechanism
