"""Error codes and messages."""


class ErrorCode:
    """Standard error codes."""

    # Validation errors
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"

    # API errors
    API_KEY_NOT_CONFIGURED = "API_KEY_NOT_CONFIGURED"
    API_REQUEST_FAILED = "API_REQUEST_FAILED"
    API_TIMEOUT = "API_TIMEOUT"
    INVALID_API_RESPONSE = "INVALID_API_RESPONSE"

    # Database errors
    DATABASE_NOT_CONFIGURED = "DATABASE_NOT_CONFIGURED"
    DATABASE_ERROR = "DATABASE_ERROR"

    # File errors
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_PARSING_FAILED = "FILE_PARSING_FAILED"

    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorMessage:
    """Standard error messages."""

    API_KEY_MISSING = "Anthropic API key not configured"
    DATABASE_MISSING = "Database not configured, running in demo mode"
    API_TIMEOUT = "Request timed out - API is taking too long to respond"
    FILE_NOT_SUPPORTED = "File type not supported. Please use PDF or DOCX"
    INTERNAL_ERROR = "Internal server error"
