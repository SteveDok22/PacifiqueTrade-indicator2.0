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