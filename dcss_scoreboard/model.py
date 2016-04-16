"""Defines the database models for this module."""

from sqlalchemy import TypeDecorator, MetaData, Table, Column
from sqlalchemy import String, Integer
import json
import sqlalchemy.ext.mutable


class JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = String

    def process_bind_param(self, value, dialect):
        """Dict -> JSON String."""
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """JSON String -> Dict."""
        return json.loads(value)

sqlalchemy.ext.mutable.MutableDict.associate_with(JsonEncodedDict)

metadata = MetaData()

game = Table('games', metadata,
             Column('gid', String, primary_key=True),
             Column('logfile', JsonEncodedDict),
)

log_progress = Table('log_progress', metadata,
                     Column('logfile', String, primary_key=True),
                     Column('lines_parsed', Integer, nullable=False))
