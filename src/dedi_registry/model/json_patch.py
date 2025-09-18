from typing import Optional
from pydantic import Field, ConfigDict

from dedi_registry.etc.enums import JsonPatchOperation
from .base import JsonModel


class JsonPatchEntry(JsonModel):
    """
    A single JSON Patch entry as per RFC 6902.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    op: JsonPatchOperation = Field(
        ...,
        description='The operation to be performed',
    )
    path: str = Field(
        ...,
        description='A JSON Pointer to the target field',
    )
    value: Optional[str | int | float | bool | list | dict] = Field(
        default=None,
        description='The value to be used in the operation. Not used for "remove" operation.',
    )
