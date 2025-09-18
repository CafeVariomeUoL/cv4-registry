from abc import ABC, abstractmethod
from typing import Literal, Annotated, Union
from pydantic import Field, ConfigDict

from dedi_registry.etc.enums import DatabaseConfigType
from .base import JsonModel


class DatabaseConfig(JsonModel):
    """
    Base class for configurations stored in the database.
    """

    model_config = ConfigDict(
        serialize_by_alias=True,
    )

    config_id: DatabaseConfigType = Field(
        ...,
        description='Unique identifier for the configuration type',
        alias='configId',
    )


class SecurityConfig(JsonModel):
    """
    Security configuration model for Dedi Registry.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    config_id: Literal[DatabaseConfigType.SECURITY] = Field(
        default=DatabaseConfigType.SECURITY,
        description='Unique identifier for the security configuration',
        alias='configId'
    )
    base_difficulty: int = Field(
        default=20,
        description='Base difficulty level for Proof of Work challenges',
        alias='baseDifficulty'
    )
    difficulty_shift: int = Field(
        default=0,
        description='Difficulty adjustment factor based on system load',
        alias='difficultyShift'
    )


DatabaseConfigUnion = Annotated[
    Union[SecurityConfig],
    Field(
        description='Database configuration type',
        discriminator='config_id'
    )
]


class ConfigRepository(ABC):
    """
    An interface for database operations related to configuration entities.
    """

    @abstractmethod
    async def get_config(self, config_type: DatabaseConfigType) -> DatabaseConfigUnion:
        """
        Retrieve a configuration by its type.

        :param config_type: The type of configuration to retrieve.
        :return: An instance of DatabaseConfig or None if not found.
        """

    @abstractmethod
    async def update_config(self, config: DatabaseConfigUnion) -> None:
        """
        Update a configuration in the database.

        :param config: An instance of DatabaseConfig to update.
        """
