"""
Custom exceptions for Sync Manager
"""


class SyncException(Exception):
    """Base exception for sync operations"""
    pass


class ConfigurationException(SyncException):
    """Configuration related exceptions"""
    pass


class NetworkException(SyncException):
    """Network related exceptions"""
    pass


class FileSystemException(SyncException):
    """File system related exceptions"""
    pass


class AuthenticationException(SyncException):
    """Authentication related exceptions"""
    pass


class ValidationException(SyncException):
    """Validation related exceptions"""
    pass


class ResourceNotFoundException(SyncException):
    """Resource not found exception"""
    pass


class PermissionException(SyncException):
    """Permission related exceptions"""
    pass


class QuotaExceededException(SyncException):
    """Quota exceeded exception"""
    pass


class RetryException(SyncException):
    """Retry related exceptions"""
    pass
