class AppException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(AppException):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field


class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, code="DATABASE_ERROR")


class ConfigurationError(AppException):
    def __init__(self, message: str):
        super().__init__(message=message, code="CONFIGURATION_ERROR")


class ExternalServiceError(AppException):
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
        )
        self.service = service


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class RateLimitError(AppException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message=message, code="RATE_LIMIT_ERROR")
