"""Defines the database models for this module."""

from sqlalchemy import TypeDecorator, MetaData, Table, Column
from sqlalchemy import String
import json
import sqlalchemy.ext.mutable

class JsonEncodedDict(TypeDecorator):
  """Enables JSON storage by encoding and decoding on the fly."""
  impl = String

  def process_bind_param(self, value, dialect):
    return json.dumps(value)

  def process_result_value(self, value, dialect):
    return json.loads(value)

sqlalchemy.ext.mutable.MutableDict.associate_with(JsonEncodedDict)

metadata = MetaData()

game = Table('games', metadata,
    Column('gid', String, primary_key=True),
    Column('logfile', JsonEncodedDict),
)
