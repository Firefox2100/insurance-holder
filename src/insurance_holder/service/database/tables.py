from sqlalchemy import Table, Column, MetaData, Integer, String, JSON


METADATA = MetaData()


CODE_CONFIG_TABLE = Table(
    'code_configs',
    METADATA,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('type', String, nullable=False),
)
