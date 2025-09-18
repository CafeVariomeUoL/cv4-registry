from abc import ABC, abstractmethod
from pydantic import Field, ConfigDict

from .base import JsonModel


class Node(JsonModel):
    """
    A node in a network, representing a DDG service instance.
    """
