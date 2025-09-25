from abc import ABC, abstractmethod

from dedi_registry.etc.consts import CONFIG
from dedi_registry.etc.enums import DatabaseDriverType
from dedi_registry.model.config import ConfigRepository
from dedi_registry.model.network import NetworkRepository, NetworkAuditRepository
from dedi_registry.model.user import UserRepository


class Database(ABC):
    """
    Unified interface for database operations.
    """

    @property
    @abstractmethod
    def config(self) -> ConfigRepository:
        """
        Get the configuration repository for managing service configurations in the database.
        :return: ConfigRepository instance.
        """

    @property
    @abstractmethod
    def networks(self) -> NetworkRepository:
        """
        Get the network repository for managing networks in the database.
        :return: NetworkRepository instance.
        """

    @property
    @abstractmethod
    def audits(self) -> NetworkAuditRepository:
        """
        Get the network audit repository for managing network audits in the database.
        :return: NetworkAuditRepository instance.
        """

    @property
    @abstractmethod
    def users(self) -> UserRepository:
        """
        Get the user repository for managing admin users in the database.
        :return: UserRepository instance.
        """

    @abstractmethod
    async def init(self):
        """
        Initialise the database by loading necessary data and constraints.

        This method should be called many times without side effects.
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database connection.
        """


_active_db: Database = None


def get_active_db() -> Database:
    """
    Return the active database set by configuration
    :return: Database instance based on the configuration.
    """
    global _active_db

    if _active_db is not None:
        return _active_db

    if CONFIG.database_driver == DatabaseDriverType.MONGO:
        from pymongo import AsyncMongoClient
        from .mongo_driver import MongoDatabase

        mongo_client = AsyncMongoClient(
            host=CONFIG.mongodb_host,
            port=CONFIG.mongodb_port,
            uuidRepresentation='standard',
        )
        MongoDatabase.set_client(
            client=mongo_client,
        )

        _active_db = MongoDatabase()

        return _active_db

    raise ValueError(
        f'Unsupported database driver: {CONFIG.database_driver}'
    )
