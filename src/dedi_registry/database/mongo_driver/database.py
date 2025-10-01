from pymongo import AsyncMongoClient

from dedi_registry.etc.consts import CONFIG, PH
from dedi_registry.model.user import User
from ..database import Database
from .config import MongoConfigRepository
from .network import MongoNetworkRepository, MongoNetworkAuditRepository
from .user import MongoUserRepository


class MongoDatabase(Database):
    """
    MongoDB implementation of the Database interface.
    """
    _client: AsyncMongoClient = None

    def __init__(self,
                 client: AsyncMongoClient = None,
                 ):
        """
        Initialise the MongoDatabase with an AsyncMongoClient instance.
        :param client: AsyncMongoClient instance.
        """
        if client is not None:
            self._client = client

    @property
    def db(self):
        """
        Get the MongoDB database instance.
        :return: The MongoDB database instance.
        """
        if self._client is None:
            raise ValueError('MongoDB client is not set. Call set_client() first.')
        return self._client[CONFIG.mongodb_db_name]

    @property
    def config(self) -> MongoConfigRepository:
        """
        Get the configuration repository for managing service configurations in the database.
        :return: ConfigRepository instance.
        """
        return MongoConfigRepository(self.db)

    @property
    def networks(self) -> MongoNetworkRepository:
        """
        Get the network repository for managing networks in the database.
        :return: NetworkRepository instance.
        """
        return MongoNetworkRepository(self.db)

    @property
    def audits(self) -> MongoNetworkAuditRepository:
        """
        Get the network audit repository for managing network audits in the database.
        :return: NetworkAuditRepository instance.
        """
        return MongoNetworkAuditRepository(self.db)

    @property
    def users(self) -> MongoUserRepository:
        """
        Get the user repository for managing admin users in the database.
        :return: MongoUserRepository instance.
        """
        return MongoUserRepository(self.db)

    @classmethod
    def set_client(cls,
                   client: AsyncMongoClient,
                   ):
        """
        Set the MongoDB client for the database.
        :param client: AsyncMongoClient instance.
        """
        cls._client = client

    async def init(self):
        """
        Initialise the MongoDB by loading necessary data and constraints.

        This method should be called many times without side effects.
        """
        user_count = await self.db.users.count_documents({})

        if user_count == 0 and CONFIG.admin_username is not None and CONFIG.admin_password is not None:
            # Create the initial admin user
            initial_admin = User(
                username=CONFIG.admin_username,
                password=PH.hash(CONFIG.admin_password),
            )

            await self.users.save(initial_admin)

    async def close(self) -> None:
        """
        Close the MongoDB connection.
        """
        if self._client is not None:
            await self._client.close()
        else:
            raise ValueError('MongoDB client is not set. Cannot close connection.')
