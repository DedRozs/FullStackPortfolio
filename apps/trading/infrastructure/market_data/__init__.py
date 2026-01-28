"""Market data clients for the Trading bounded context.

LocalMarketDataService is the primary data source for the content pipeline.
It reads from stored 1-minute bars (fetched from Databento) and computes
daily/weekly/monthly aggregates locally.

MarketDataSyncService handles on-demand fetching from Databento when
local data is missing. It ensures data freshness before content generation.

YFinanceClient is deprecated and should not be used for new code.
"""
from apps.trading.infrastructure.market_data.local_market_data import (
    LocalMarketDataService,
    SessionData,
    OvernightData,
    DataNotAvailableError,
    get_local_market_data_service,
)
from apps.trading.infrastructure.market_data.sync_service import (
    MarketDataSyncService,
    DataFetchError,
)

# Deprecated - kept for backward compatibility during migration
from apps.trading.infrastructure.market_data.yfinance_client import (
    YFinanceClient,
    MarketDataClient,
    get_yfinance_client,
)

__all__ = [
    # Primary (use these)
    'LocalMarketDataService',
    'SessionData',
    'OvernightData',
    'DataNotAvailableError',
    'get_local_market_data_service',
    # Sync service for auto-fetching
    'MarketDataSyncService',
    'DataFetchError',
    # Deprecated (do not use)
    'YFinanceClient',
    'MarketDataClient',
    'get_yfinance_client',
]
