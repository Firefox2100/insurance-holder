from enum import Enum, StrEnum


class CodeEffect(Enum):
    PACIFY = 'pacify'
    TRIGGER = 'trigger'
    SILENT_TRIGGER = 'silentTrigger'


class CodeType(StrEnum):
    STATIC = 'static'
    TOTP = 'totp'


class CountdownStatus(Enum):
    DISABLED = 'disabled'
    HEALTHY = 'healthy'
    NOTIFYING = 'notifying'
    DUE = 'due'
    TRIGGERED = 'triggered'
