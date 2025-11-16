"""
Custom exceptions for PacifiqueTrade Indicator 2.0

Defines all custom exception types used throughout the system
for better error handling and debugging.
"""


class PacifiqueTradeError(Exception):
    """Base exception for all PacifiqueTrade errors"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class APIError(PacifiqueTradeError):
    """Raised when an external API call fails"""
    
    def __init__(self, api_name: str, message: str, status_code: int = None, details: dict = None):
        self.api_name = api_name
        self.status_code = status_code
        full_message = f"API Error [{api_name}]: {message}"
        if status_code:
            full_message += f" (Status: {status_code})"
        super().__init__(full_message, details)
        
class DataValidationError(PacifiqueTradeError):
    """Raised when data validation fails"""
    
    def __init__(self, field_name: str, value, expected: str = None, details: dict = None):
        self.field_name = field_name
        self.value = value
        self.expected = expected
        message = f"Data validation failed for '{field_name}': got {value}"
        if expected:
            message += f", expected {expected}"
        super().__init__(message, details)


class ConfigurationError(PacifiqueTradeError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, config_key: str, message: str = None, details: dict = None):
        self.config_key = config_key
        if message is None:
            message = f"Configuration error for '{config_key}': missing or invalid value"
        else:
            message = f"Configuration error for '{config_key}': {message}"
        super().__init__(message, details)        
        
class SignalGenerationError(PacifiqueTradeError):
    """Raised when signal generation fails"""
    
    def __init__(self, reason: str, pair: str = None, details: dict = None):
        self.reason = reason
        self.pair = pair
        message = f"Signal generation failed: {reason}"
        if pair:
            message += f" for {pair}"
        super().__init__(message, details)


class MarketDataError(PacifiqueTradeError):
    """Raised when market data fetching or processing fails"""
    
    def __init__(self, pair: str, timeframe: str, message: str, details: dict = None):
        self.pair = pair
        self.timeframe = timeframe
        full_message = f"Market data error for {pair} ({timeframe}): {message}"
        super().__init__(full_message, details)


class TelegramError(PacifiqueTradeError):
    """Raised when Telegram notification fails"""
    
    def __init__(self, message: str, chat_id: str = None, details: dict = None):
        self.chat_id = chat_id
        full_message = f"Telegram error: {message}"
        if chat_id:
            full_message += f" (Chat ID: {chat_id})"
        super().__init__(full_message, details)


class RiskManagementError(PacifiqueTradeError):
    """Raised when risk management calculations fail"""
    
    def __init__(self, message: str, account_balance: float = None, details: dict = None):
        self.account_balance = account_balance
        full_message = f"Risk management error: {message}"
        if account_balance:
            full_message += f" (Account: ${account_balance})"
        super().__init__(full_message, details)        
        
class SchedulerError(PacifiqueTradeError):
    """Raised when scheduler encounters an error"""
    
    def __init__(self, job_name: str, message: str, details: dict = None):
        self.job_name = job_name
        full_message = f"Scheduler error for job '{job_name}': {message}"
        super().__init__(full_message, details)


class CacheError(PacifiqueTradeError):
    """Raised when cache operations fail"""
    
    def __init__(self, operation: str, key: str = None, message: str = None, details: dict = None):
        self.operation = operation
        self.key = key
        if message is None:
            message = f"Cache {operation} failed"
        else:
            message = f"Cache {operation} failed: {message}"
        if key:
            message += f" (Key: {key})"
        super().__init__(message, details)


class TrendDetectionError(PacifiqueTradeError):
    """Raised when trend detection fails"""
    
    def __init__(self, pair: str, timeframe: str, reason: str, details: dict = None):
        self.pair = pair
        self.timeframe = timeframe
        self.reason = reason
        message = f"Trend detection failed for {pair} ({timeframe}): {reason}"
        super().__init__(message, details)


class LiquidityZoneError(PacifiqueTradeError):
    """Raised when liquidity zone detection fails"""
    
    def __init__(self, pair: str, zone_type: str, reason: str, details: dict = None):
        self.pair = pair
        self.zone_type = zone_type
        self.reason = reason
        message = f"Liquidity zone detection ({zone_type}) failed for {pair}: {reason}"
        super().__init__(message, details)        
        
class InsufficientDataError(PacifiqueTradeError):
    """Raised when there's not enough data for analysis"""
    
    def __init__(self, required: int, available: int, data_type: str, details: dict = None):
        self.required = required
        self.available = available
        self.data_type = data_type
        message = f"Insufficient {data_type}: need {required} bars, got {available}"
        super().__init__(message, details)


class TimeoutError(PacifiqueTradeError):
    """Raised when an operation times out"""
    
    def __init__(self, operation: str, timeout_seconds: int, details: dict = None):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, details)


# Exception mapping for retry logic
RETRYABLE_EXCEPTIONS = (
    APIError,
    MarketDataError,
    CacheError,
    TimeoutError,
)

NON_RETRYABLE_EXCEPTIONS = (
    ConfigurationError,
    DataValidationError,
    InsufficientDataError,
)        