from abc import ABC, abstractmethod
from uuid import UUID
from pydantic import Field, ConfigDict

from .base import JsonModel


class Node(JsonModel):
    """
    A node in a network, representing a DDG service instance.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )
    node_id: UUID = Field(
        ...,
        alias='nodeId',
        description='The unique ID of the node. Should be UUID4 format.'
    )
    node_name: str = Field(
        ...,
        alias='nodeName',
        description='The name of the node'
    )
    url: str = Field(
        ...,
        description='The base URL of the node'
    )
    description: str = Field(
        default='',
        description='A description of the node'
    )
    public_key: str = Field(
        ...,
        alias='publicKey',
        description='The public key of the node in a network, in PEM format'
    )
