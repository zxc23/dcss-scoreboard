"""Defines the database models for this module."""

import json
import collections
import sqlalchemy.ext.mutable
import datetime

from sqlalchemy import TypeDecorator, MetaData, Table, Column, String, Integer, Boolean, DateTime
from . import modelutils


class DatabaseError(Exception):
    """Generic error for issues with the model."""
    pass


def sqlite_performance_over_safety(dbapi_con, con_record):
    """Significantly speeds up inserts but will break on crash."""
    dbapi_con.execute('PRAGMA journal_mode = MEMORY')
    dbapi_con.execute('PRAGMA synchronous = OFF')


def deque_default(obj):
    """Convert deques to lists.

    Used to persist deque data into JSON.
    """
    if isinstance(obj, collections.deque):
        return list(obj)
    raise TypeError


class _JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = String

    def process_bind_param(self, value, dialect):
        """Dict -> JSON String."""
        return json.dumps(value, default=deque_default)

    def process_result_value(self, value, dialect):
        """JSON String -> Dict."""
        return json.loads(value)


sqlalchemy.ext.mutable.MutableDict.associate_with(_JsonEncodedDict)

_metadata = MetaData()

_games = Table('games',
               _metadata,
               Column('gid',
                      String,
                      primary_key=True),
               Column('name',
                      String,
                      nullable=False),
               Column('start',
                      sqlalchemy.types.DateTime,
                      nullable=False),
               Column('end',
                      sqlalchemy.types.DateTime,
                      nullable=False),
               Column('raw_data',
                      _JsonEncodedDict,
                      nullable=False),
               Column('scored',
                      Boolean,
                      default=False))

_logfile_progress = Table('logfile_progress',
                          _metadata,
                          Column('logfile',
                                 String,
                                 primary_key=True),
                          Column('lines_parsed',
                                 Integer,
                                 nullable=False))

_player_stats = Table('player_stats',
                      _metadata,
                      Column('name',
                             String,
                             primary_key=True),
                      Column('stats',
                             _JsonEncodedDict,
                             nullable=False))

_global_stats = Table('global_stats',
                      _metadata,
                      Column('key',
                             String,
                             primary_key=True),
                      Column('data',
                             _JsonEncodedDict,
                             nullable=False))

_engine = sqlalchemy.create_engine('sqlite:///database.db', echo=False)
sqlalchemy.event.listen(_engine, 'connect', sqlite_performance_over_safety)
_metadata.create_all(_engine)
_conn = _engine.connect()


def add_game(gid, raw_data):
    """Add a game to the database."""
    try:
        name = raw_data['name']
        start = modelutils.prettycrawldate(raw_data['start'], return_datetime=True)
        end = modelutils.prettycrawldate(raw_data['end'], return_datetime=True)
        type(start)
        _conn.execute(_games.insert(),
                      gid=gid,
                      name=name,
                      start=start,
                      end=end,
                      raw_data=raw_data)
    except sqlalchemy.exc.IntegrityError:
        raise DatabaseError("Duplicate game %s, ignoring." % gid)


def get_logfile_pos(logfile):
    """Get the number of lines we've already processed."""
    s = _logfile_progress.select().where(_logfile_progress.c.logfile ==
                                         logfile)
    row = _conn.execute(s).fetchone()
    if row:
        return row.lines_parsed
    else:
        return 0


def save_logfile_pos(logfile, pos):
    """Save the number of lines we've processed."""
    # print("Saving log pos for", logfile, "as", pos)
    # XXX instead of this try: except:, see if
    # prefixes="OR REPLACE" works
    # http://docs.sqlalchemy.org/en/rel_1_0/core/dml.html#
    #                                       sqlalchemy.sql.expression.insert
    try:
        _conn.execute(_logfile_progress.insert(),
                      logfile=logfile,
                      lines_parsed=pos)
    except sqlalchemy.exc.IntegrityError:
        _conn.execute(_logfile_progress.update().where(
            _logfile_progress.c.logfile == logfile).values(lines_parsed=pos))


def players():
    """Return list of all players.

    XXX should be at least memoised if not outright replaced with something
    saner.
    """
    return [i.name for i in get_all_player_stats()]


def get_all_player_stats():
    """Return all rows in player_stats table.

    XXX should be at least memoised if not outright replaced with something
    saner.
    """
    s = _player_stats.select()
    return _conn.execute(s).fetchall()


def delete_all_player_stats():
    """Deletes all player stats."""
    _conn.execute(_player_stats.delete())


def delete_player_stats(name):
    """Deletes a player's stats."""
    _conn.execute(_player_stats.delete().where(_player_stats.c.name == name))


def get_player_stats(name):
    """Return a dict of the player's current stats.

    If the player doesn't exist, None is returned.
    """
    s = _player_stats.select().where(_player_stats.c.name == name)
    result = _conn.execute(s).fetchone()
    if result:
        score = result[1]
    else:
        score = None
    return score


def set_player_stats(name, stats):
    """Write player's stats to the database.

    XXX this function is the slowest part of scoring.py.
    """
    # print("Saving scoring data for", player)
    try:
        _conn.execute(_player_stats.insert(), name=name, stats=stats)
    except sqlalchemy.exc.IntegrityError:
        _conn.execute(_player_stats.update().where(_player_stats.c.name ==
                                                   name).values(stats=stats))


def get_all_games(scored=None):
    """Return all games.

    If scored is not none, only return games who match bool(scored).
    Games are ordered by end datetime.

    Note: Uses a lot of RAM if there are a lot of games.
    XXX fix this.
    """
    s = _games.select()
    if scored is not None:
        s = s.where(_games.c.scored == bool(scored)).order_by(_games.c.end.asc())
    return _conn.execute(s).fetchall()


def mark_game_scored(gid):
    """Mark a game as being scored."""
    s = _games.update().where(_games.c.gid == gid).values(scored=True)
    _conn.execute(s)


def unscore_all_games():
    """Marks all games as being unscored."""
    _conn.execute(_games.update().values(scored=False))


def unscore_all_games_of_player(name):
    """Marks all games by a player as being unscored."""
    _conn.execute(_games.update().where(_games.c.name == name).values(scored=
                                                                      False))


def set_global_stat(key, data):
    """Set global stat data."""
    try:
        _conn.execute(_global_stats.insert(), key=key, data=data)
    except sqlalchemy.exc.IntegrityError:
        _conn.execute(_global_stats.update().where(_global_stats.c.key ==
                                                   key).values(data=data))


def get_global_stat(key):
    """Get global score data."""
    s = _global_stats.select().where(_global_stats.c.key == key)
    val = _conn.execute(s).fetchone()
    if val is not None:
        return val[1]
    else:
        return None


def get_all_global_stats():
    """Get all global score data."""
    scores = {}
    s = _global_stats.select()
    for row in _conn.execute(s).fetchall():
        scores[row[0]] = row[1]
    return scores
