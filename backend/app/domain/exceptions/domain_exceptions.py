# Domain Layer Exceptions

class DomainException(Exception):
    """Exception base para toda la capa de dominio"""
    pass


class EntityNotFound(DomainException):
    """Entidad no encontrada"""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con ID {entity_id} no encontrado")


class InvalidEntity(DomainException):
    """Entidad con datos inválidos"""
    def __init__(self, entity_type: str, reason: str):
        self.entity_type = entity_type
        self.reason = reason
        super().__init__(f"{entity_type} inválido: {reason}")


class DuplicateEntity(DomainException):
    """Entidad duplicada"""
    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} con {field}={value} ya existe")


class PermissionDenied(DomainException):
    """Permiso denegado"""
    def __init__(self, user_id: str, action: str, resource_id: str):
        self.user_id = user_id
        self.action = action
        self.resource_id = resource_id
        super().__init__(f"Usuario {user_id} no tiene permiso para {action} en {resource_id}")


class InvalidOperation(DomainException):
    """Operación inválida"""
    def __init__(self, message: str):
        super().__init__(message)


class DocumentProcessingError(DomainException):
    """Error durante procesamiento de documento"""
    def __init__(self, document_id: str, stage: str, reason: str):
        self.document_id = document_id
        self.stage = stage
        self.reason = reason
        super().__init__(f"Error procesando {document_id} en stage {stage}: {reason}")
