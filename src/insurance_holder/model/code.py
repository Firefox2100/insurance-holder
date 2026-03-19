from typing import Literal, Optional, Union, Annotated
from pydantic import Field, ConfigDict

from insurance_holder.etc.consts import PH
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

    def to_storage(self) -> dict:
        """
        Converts the instance into a storage-compatible dictionary format.
        :return: A dictionary that can be used for persistence or further processing.
        :raises NotImplementedError: This method is not implemented on this class.
        """
        raise NotImplementedError


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

    def to_storage(self) -> dict:
        """
        Converts the instance into a storage-compatible dictionary format.
        :return: A dictionary that can be used for persistence or further processing.
        """
        return {
            'hash': self.code_hash,
        }


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

    code_id: Optional[int] = Field(
        None,
        description='The unique identifier of the code.',
        alias='codeId',
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

    def to_storage(self) -> dict:
        payload = {
            'type': self.code.code_type.value,
            'effect': self.effect.value,
            'delay': self.delay,
        }

        payload.update(self.code.to_storage())

        return payload

    @classmethod
    def from_storage(cls, payload: dict) -> 'CodeConfig':
        code_type = CodeType(payload['type'])
        if code_type == CodeType.STATIC:
            code = StaticCode(
                codeType=code_type,
                codeHash=payload['hash'],
            )
        else:
            raise ValueError(f'Unknown code type: {code_type.value}')

        return CodeConfig(
            codeId=payload['codeId'],
            code=code,
            effect=CodeEffect(payload['effect']),
            delay=payload['delay'],
        )


class CreateCodeConfig(JsonModel):
    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    code_type: CodeType = Field(
        ...,
    )
    static_value: Optional[str] = Field(
        None,
        alias='staticValue',
    )
    effect: CodeEffect = Field(
        ...,
    )
    delay: Optional[int] = Field(
        None,
    )

    def to_code_config(self):
        if self.code_type == CodeType.STATIC:
            if not self.static_value:
                raise ValueError('A value must be provided for static code.')
            code = StaticCode(
                codeType=CodeType.STATIC,
                codeHash=PH.hash(self.static_value),
            )
        else:
            raise ValueError(f'Unknown code type: {self.code_type.value}')

        return CodeConfig(
            codeId=None,
            code=code,
            effect=self.effect,
            delay=None if self.effect == CodeEffect.PACIFY else self.delay,
        )
