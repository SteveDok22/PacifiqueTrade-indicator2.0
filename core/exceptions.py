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