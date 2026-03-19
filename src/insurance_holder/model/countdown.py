import time
from uuid import uuid4
from typing import Optional
from pydantic import Field, ConfigDict

from insurance_holder.etc.enums import CountdownStatus
from insurance_holder.model.base import JsonModel
from insurance_holder.model.code import CodeConfig, CreateCodeConfig


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
        alias='gracePeriod',
    )
    enabled: bool = Field(
        True,
        description='Whether the countdown is enabled and actions should be triggered.',
    )
    public: bool = Field(
        False,
        description='Whether the countdown should be publicly visible or not.',
    )
    name: str = Field(
        ...,
        description='Name of the countdown, will be displayed on the interface.'
    )
    description: Optional[str] = Field(
        None,
        description='Description of the countdown, will be displayed on the interface.'
    )
    codes: list[CodeConfig] = Field(
        default_factory=list,
        description='A list of codes configured for this countdown.',
    )

    def to_storage(self):
        payload = {
            'id': self.countdown_id,
            'time': self.countdown_time,
            'notification_period': self.notification_period,
            'grace_period': self.grace_period,
            'enabled': self.enabled,
            'public': self.public,
            'name': self.name,
            'description': self.description,
        }

        return payload

    @classmethod
    def from_storage(cls, payload: dict) -> 'Countdown':
        return cls(
            countdownId=payload['id'],
            countdownTime=payload['time'],
            notificationPeriod=payload['notification_period'],
            gracePeriod=payload['grace_period'],
            enabled=payload['enabled'],
            public=payload['public'],
            name=payload['name'],
            description=payload['description'],
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

    def to_storage(self) -> dict:
        payload = {
            'id': self.countdown_id,
            'public_status': self.public_status.value if self.public_status else None,
            'status': self.status.value,
            'version': self.version,
            'next_trigger_at': self.next_trigger_at,
        }

        return payload

    @classmethod
    def from_storage(cls, payload: dict) -> 'CountdownState':
        return cls(
            countdownId=payload['id'],
            publicStatus=CountdownStatus(payload['public_status']) if payload['public_status'] else None,
            status=CountdownStatus(payload['status']),
            version=payload['version'],
            nextTriggerAt=payload['next_trigger_at'],
        )


class CreateCountdown(JsonModel):
    name: str = Field(
        ...,
    )
    description: Optional[str] = Field(
        None,
    )
    enabled: bool = Field(
        True,
    )
    public: bool = Field(
        False,
    )
    time: int = Field(
        ...,
    )
    notification: Optional[int] = Field(
        None,
    )
    grace: Optional[int] = Field(
        None,
    )
    first_run: Optional[int] = Field(
        None,
        alias='firstRun'
    )
    codes: list[CreateCodeConfig] = Field(
        default_factory=list,
        min_length=1,
    )

    def to_countdown(self):
        return Countdown(
            name=self.name,
            description=self.description,
            enabled=self.enabled,
            public=self.public,
            countdownTime=self.time,
            notificationPeriod=self.notification,
            gracePeriod=self.grace,
            codes=[c.to_code_config() for c in self.codes]
        ), self.first_run


def calculate_current_state(countdown: Countdown,
                            countdown_state: CountdownState,
                            ) -> CountdownState:
    if not countdown.enabled:
        # States won't update if it's not running
        return countdown_state

    notification_threshold = countdown_state.next_trigger_at - (countdown.notification_period or 0)
    trigger_threshold = countdown_state.next_trigger_at + (countdown.grace_period or 0)

    current_time = int(time.time())

    if current_time < notification_threshold:
        # Healthy
        if countdown_state.status == CountdownStatus.HEALTHY:
            return countdown_state

        return CountdownState(
            countdownId=countdown_state.countdown_id,
            # Public status can only be healthy override for safety reasons
            publicStatus=CountdownStatus.HEALTHY if countdown_state.public_status is not None else None,
            status=CountdownStatus.HEALTHY,
            version=countdown_state.version + 1,
            nextTriggerAt=countdown_state.next_trigger_at,
        )

    if current_time < countdown_state.next_trigger_at:
        # Notification needed
        if countdown_state.status == CountdownStatus.NOTIFYING:
            return countdown_state

        return CountdownState(
            countdownId=countdown_state.countdown_id,
            publicStatus=countdown_state.public_status,
            status=CountdownStatus.NOTIFYING,
            version=countdown_state.version + 1,
            nextTriggerAt=countdown_state.next_trigger_at,
        )

    if current_time < trigger_threshold:
        # Due, still in grace period
        if countdown_state.status == CountdownStatus.DUE:
            return countdown_state

        return CountdownState(
            countdownId=countdown_state.countdown_id,
            publicStatus=countdown_state.public_status,
            status=CountdownStatus.DUE,
            version=countdown_state.version + 1,
            nextTriggerAt=countdown_state.next_trigger_at,
        )

    # Need to trigger action
    if countdown_state.status == CountdownStatus.TRIGGERED:
        return countdown_state

    return CountdownState(
        countdownId=countdown_state.countdown_id,
        publicStatus=countdown_state.public_status,
        status=CountdownStatus.TRIGGERED,
        version=countdown_state.version + 1,
        nextTriggerAt=countdown_state.next_trigger_at,
    )
