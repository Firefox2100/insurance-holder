from uuid import uuid4
from typing import Optional
from pydantic import Field, ConfigDict

from insurance_holder.etc.enums import CountdownStatus
from insurance_holder.model.base import JsonModel


class Countdown(JsonModel):
    """
    A countdown is a core trigger of a series of events if left till finished.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    countdown_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description='The ID of the countdown, in UUID4 format.',
        alias='countdownId',
    )
    countdown_time: int = Field(
        ...,
        description='The time for the countdown to finish, in seconds.',
        alias='countdownTime',
    )
    notification_period: Optional[int] = Field(
        None,
        description='How long before the countdown due should user be notified, in seconds. If not set, '
                    'user will not be notified before countdown is due.',
        alias='notificationPeriod',
    )
    grace_period: Optional[int] = Field(
        None,
        description='How long after the countdown is due must the action be triggered, in seconds. If not set, '
                    'action will be triggered immediately after the countdown finishes.',
    )
    enabled: bool = Field(
        True,
        description='Whether the countdown is enabled and actions should be triggered.',
    )
    public: bool = Field(
        False,
        description='Whether the countdown should be publicly visible or not.',
    )


class CountdownState(JsonModel):
    """
    The current state of a countdown. This is used as a source of truth in the database.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    countdown_id: str = Field(
        ...,
        description='The ID of the countdown, in UUID4 format.',
        alias='countdownId',
    )
    public_status: Optional[CountdownStatus] = Field(
        None,
        description='The status of the countdown that is safe to be exposed to the public. This is '
                    'used for display purposes only and should not be used for any logic.',
        alias='publicStatus',
    )
    status: CountdownStatus = Field(
        ...,
        description='The actual status of the countdown.',
    )
    version: int = Field(
        ...,
        description='The monotonic version of the countdown status.',
    )
    next_trigger_at: Optional[int] = Field(
        None,
        description='The next trigger time for the countdown, in seconds since epoch.',
        alias='nextTriggerAt',
    )
