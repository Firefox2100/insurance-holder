from sqlalchemy import Table, Column, MetaData, Integer, Boolean, String, ForeignKey


METADATA = MetaData()


COUNTDOWN_TABLE = Table(
    'countdown',
    METADATA,
    Column('id', String, primary_key=True, nullable=False),
    Column('time', Integer, nullable=False),
    Column('notification_period', Integer, nullable=True),
    Column('grace_period', Integer, nullable=True),
    Column('enabled', Boolean, nullable=False, default=True),
    Column('public', Boolean, nullable=False, default=False),
    Column('name', String, nullable=False),
    Column('description', String, nullable=True),
)


COUNTDOWN_STATE_TABLE = Table(
    'countdown_state',
    METADATA,
    Column('id', String, ForeignKey('countdown.id'), primary_key=True, nullable=False),
    Column('public_status', String, nullable=True),
    Column('status', String, nullable=False),
    Column('version', Integer, nullable=False),
    Column('next_trigger_at', Integer, nullable=True)
)


CODE_CONFIG_TABLE = Table(
    'code_config',
    METADATA,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('countdown_id', String, ForeignKey('countdown.id'), nullable=False),
    Column('type', String, nullable=False),
    Column('effect', String, nullable=False),
    Column('delay', Integer, nullable=True),
    Column('hash', String, nullable=True),
)
