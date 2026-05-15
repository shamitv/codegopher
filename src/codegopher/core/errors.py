"""Error types used across CodeGopher."""

from __future__ import annotations


class CodeGopherError(Exception):
    """Base class for user-facing CodeGopher failures."""


class ConfigurationError(CodeGopherError):
    """Raised when settings cannot be loaded or validated."""


class ProviderError(CodeGopherError):
    """Raised when a model provider fails or is misconfigured."""


class ToolExecutionError(CodeGopherError):
    """Raised when a tool cannot execute its requested operation."""


class ApprovalError(CodeGopherError):
    """Raised when approval is required but unavailable or denied."""


class AgentLoopError(CodeGopherError):
    """Raised when the core agent loop cannot complete."""
