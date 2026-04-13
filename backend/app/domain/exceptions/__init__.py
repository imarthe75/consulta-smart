# Base Module Initialization

from .domain_exceptions import (
    DomainException,
    EntityNotFound,
    InvalidEntity,
    DuplicateEntity,
    PermissionDenied,
    InvalidOperation,
    DocumentProcessingError
)

__all__ = [
    'DomainException',
    'EntityNotFound',
    'InvalidEntity',
    'DuplicateEntity',
    'PermissionDenied',
    'InvalidOperation',
    'DocumentProcessingError'
]
