class ServiceError(Exception):
    """Base class for business-rule errors raised by services."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFound(ServiceError):
    """Mapped to HTTP 404."""


class Conflict(ServiceError):
    """Mapped to HTTP 409."""


class ValidationFailed(ServiceError):
    """Mapped to HTTP 422."""
