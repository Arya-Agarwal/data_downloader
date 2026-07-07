"""
Live Market Data Module

This package contains all components required for collecting,
processing, buffering and storing live market data from Zerodha.

Responsibilities:

- WebSocket connection management
- Subscription management
- Tick routing
- Tick buffering
- Live parquet writing
- Market depth storage
- Derived option chain snapshots
- Live tracker

Historical downloading remains completely independent from this package.
"""