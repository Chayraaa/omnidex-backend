class SummaryError(Exception):
    """Base class for summary-related errors."""


class SummaryUnavailable(SummaryError):
    """Raised when the summary provider is unavailable."""


class InvalidSummaryResponse(SummaryError):
    """Raised when the summary provider returns invalid content."""
