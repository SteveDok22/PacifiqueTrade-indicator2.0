"""
Scheduler module for PacifiqueTrade Indicator 2.0

This module handles automated job scheduling:
- Pre-market analysis (T-4h)
- Technical confirmation (T-2h)
- Signal generation (T-15min)
- Market reaction monitoring (T-0)
- Automated Telegram alerts
"""

from .job_scheduler import JobScheduler, TradingJob

__all__ = [
    'JobScheduler',
    'TradingJob',
]

__version__ = '2.0.0'