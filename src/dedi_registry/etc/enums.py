from enum import Enum, StrEnum


class CacheDriverType(Enum):
    """
    Types of cache drivers that can be configured in the application.
    """
    MEMORY = 'memory'
    REDIS = 'redis'


class DatabaseConfigType(StrEnum):
    """
    Types of configurations that can be stored in the database.
    """
    SECURITY = 'security'


class DatabaseDriverType(Enum):
    """
    Types of database drivers that can be configured in the application.
    """
    MONGO = 'mongo'


class JsonPatchOperation(Enum):
    """
    Operations that can be performed in a JSON Patch.
    """
    ADD = 'add'
    REMOVE = 'remove'
    REPLACE = 'replace'
    MOVE = 'move'
    COPY = 'copy'
    TEST = 'test'


class RecordAction(Enum):
    """
    Actions that can be performed on a record.
    """
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    APPROVE = 'approve'
    REJECT = 'reject'
    BLACKLIST = 'blacklist'


class RecordStatus(Enum):
    """
    Status of a record in the system.
    """
    PENDING = 'pending'         # Pending review or approval
    ACTIVE = 'active'           # Active and available for use and query
    REJECTED = 'rejected'       # Rejected, but archived for record-keeping
    BLACKLISTED = 'blacklisted' # Blacklisted, all relevant resources are restricted (i.e. domain, IP)
