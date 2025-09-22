from abc import ABC, abstractmethod
from pydantic import Field, ConfigDict

from .base import JsonModel


class User(JsonModel):
    """
    A model for an admin user in the system
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    username: str = Field(
        ...,
        description='The username of the user.',
    )
    password: str = Field(
        ...,
        description='The password of the user. Stored in database as argon 2 hash.',
    )


class UserRepository(ABC):
    """
    An interface for database operations related to Network entities.
    """

    @abstractmethod
    async def get(self, username: str) -> User | None:
        """
        Retrieve a user by their username.
        :param username: The username of the user to retrieve.
        :return: User object or None if not found.
        """
