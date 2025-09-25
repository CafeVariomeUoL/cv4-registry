from pymongo.asynchronous.database import AsyncDatabase

from dedi_registry.model.user import User, UserRepository


class MongoUserRepository(UserRepository):
    """
    MongoDB implementation of the UserRepository interface.
    """

    def __init__(self, db: AsyncDatabase):
        """
        Initialise the MongoUserRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        """
        self.db = db
        self.collection = db['users']

    async def get(self, username: str) -> User | None:
        """
        Retrieve a user by their username.
        :param username: The username of the user to retrieve.
        :return: User object or None if not found.
        """
        document = await self.collection.find_one({'username': username}, {'_id': 0})

        if document:
            return User.model_validate(document)

        return None

    async def filter(self) -> list[User]:
        """
        Get a list of all User entities.
        :return: A list of User instances.
        """
        cursor = self.collection.find({}, {'_id': 0})
        users = []
        async for document in cursor:
            users.append(User.model_validate(document))
        return users

    async def save(self, user: User):
        """
        Save a User entity to the database.
        :param user: An instance of User to be saved.
        """
        data = user.model_dump(by_alias=True)
        await self.collection.update_one(
            {'username': user.username},
            {'$set': data},
            upsert=True
        )

    async def update(self, user: User):
        """
        Update an existing User entity in the database.
        :param user: An instance of User to be updated.
        """
        data = user.model_dump(by_alias=True)
        await self.collection.update_one(
            {'username': user.username},
            {'$set': data}
        )

    async def delete(self, username: str):
        """
        Delete a User entity from the database.
        :param username: The username of the user to be deleted.
        """
        await self.collection.delete_one({'username': username})
