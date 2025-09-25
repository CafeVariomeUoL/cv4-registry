from abc import ABC, abstractmethod
from argon2.exceptions import VerifyMismatchError
from pydantic import Field, ConfigDict

from dedi_registry.etc.consts import PH
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

    def validate_password(self, password: str) -> bool:
        """
        Validate the provided password against the stored password hash.
        :param password: The password to validate.
        :return: True if the password is valid, False otherwise.
        """
        try:
            PH.verify(self.password, password)
            return True
        except VerifyMismatchError:
            return False


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

    @abstractmethod
    async def filter(self) -> list[User]:
        """
        Get a list of all User entities.
        :return: A list of User instances.
        """

    @abstractmethod
    async def save(self, user: User):
        """
        Save a User entity to the database.
        :param user: An instance of User to be saved.
        """

    @abstractmethod
    async def update(self, user: User):
        """
        Update an existing User entity in the database.
        :param user: An instance of User to be updated.
        """

    @abstractmethod
    async def delete(self, username: str):
        """
        Delete a User entity from the database.
        :param username: The username of the user to be deleted.
        """
