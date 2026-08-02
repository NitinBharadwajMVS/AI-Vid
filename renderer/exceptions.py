"""
Renderer Custom Exceptions.

Defines custom exceptions for video rendering configuration, provider errors, and rendering pipeline failures.
"""


class RendererError(Exception):
    """Base exception for all rendering failures."""
    pass


class InvalidRendererConfiguration(RendererError):
    """Raised when rendering configuration is invalid or missing."""
    pass


class RendererProviderError(RendererError):
    """Raised when an underlying rendering engine/provider encounters an error."""
    pass
