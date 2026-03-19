from typing import Literal, Optional, Union, Annotated
from pydantic import Field, ConfigDict

from insurance_holder.etc.enums import CodeType, CodeEffect
from insurance_holder.model.base import JsonModel


class Code(JsonModel):
    """
    Base model for all code types.
    """

    model_config = ConfigDict(
        serialize_by_alias=True,
    )

    code_type: CodeType = Field(
        ...,
        description='The type of code used in checkin.',
        alias='codeType',
    )


class StaticCode(Code):
    """
    Static Code does not change between each checkin.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    code_type: Literal[CodeType.STATIC] = Field(
        CodeType.STATIC,
        description='The type of code used in checkin.',
        alias='codeType',
    )
    code_hash: str = Field(
        ...,
        description='The hash of the code used in checkin.',
        alias='codeHash',
    )


DiscriminatedCodeUnion = Annotated[
    Union[StaticCode],
    Field(
        description='Discriminated union for check in code classes.',
        discriminator='code_type',
    )
]


class CodeConfig(JsonModel):
    """
    The configuration for all code types.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    code: DiscriminatedCodeUnion = Field(
        ...,
        description='The type of code used in checkin with its content.',
    )
    effect: CodeEffect = Field(
        ...,
        description='What does this code do when entered.',
    )
    delay: Optional[int] = Field(
        None,
        description='Delay to trigger, if applicable.',
    )
