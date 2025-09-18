"""
MongoDB implementation of the ConfigRepository interface.
"""

from pydantic import TypeAdapter
from pymongo.asynchronous.database import AsyncDatabase

from dedi_registry.etc.enums import DatabaseConfigType
from dedi_registry.model.config import DatabaseConfigUnion, ConfigRepository


class MongoConfigRepository(ConfigRepository):
    """
    MongoDB implementation of the ConfigRepository interface.
    """

    def __init__(self, db: AsyncDatabase):
        """
        Initialise the MongoUserRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        """
        self.db = db
        self.collection = db['config']

    async def get_config(self, config_type: DatabaseConfigType) -> DatabaseConfigUnion:
        """
        Retrieve a configuration by its type.

        :param config_type: The type of configuration to retrieve.
        :return: An instance of DatabaseConfig or None if not found.
        """
        doc = await self.collection.find_one({'configId': config_type.value}, {'_id': 0})

        config_adapter = TypeAdapter(DatabaseConfigUnion)
        config = config_adapter.validate_python(doc or {'configId': config_type.value})

        return config

    async def update_config(self, config: DatabaseConfigUnion) -> None:
        """
        Update a configuration in the database.

        :param config: An instance of DatabaseConfig to update.
        """
        await self.collection.update_one(
            {'configId': config.config_id.value},
            {'$set': config.model_dump(by_alias=True)},
            upsert=True
        )
