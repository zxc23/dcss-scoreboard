"""Defines the database models for this module."""

import json
import collections
import sqlalchemy.ext.mutable
import datetime

from sqlalchemy import TypeDecorator, MetaData, Table, Column, String, Integer, Boolean, DateTime, LargeBinary
import _mysql_exceptions

from . import modelutils

# DB_URI = sqlite:///database.db
DB_URI = 'mysql://localhost/dcss_scoreboard'


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

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        """Dict -> JSON String."""
        return json.dumps(value, default=deque_default).encode()

    def process_result_value(self, value, dialect):
        """JSON String -> Dict."""
        return json.loads(value.decode())


sqlalchemy.ext.mutable.MutableDict.associate_with(_JsonEncodedDict)

_metadata = MetaData()

_games = Table('games',
               _metadata,
               Column('gid',
                      String(50),
                      primary_key=True),
               Column('name',
                      String(50),  # XXX: is this long enough?
                      nullable=False),
               Column('start',
                      sqlalchemy.types.DateTime,
                      nullable=False),
               Column('end',
                      sqlalchemy.types.DateTime,
                      nullable=False),
               Column('runes',
                      Integer,
                      nullable=False),
               Column('raw_data',
                      _JsonEncodedDict(10000),
                      nullable=False),
               Column('scored',
                      Boolean,
                      default=False),
               mysql_engine='InnoDB',
               mysql_charset='utf8')

_logfile_progress = Table('logfile_progress',
                          _metadata,
                          Column('logfile',
                                 String(100),
                                 primary_key=True),
                          Column('lines_parsed',
                                 Integer,
                                 nullable=False),
                          mysql_engine='InnoDB',
                          mysql_charset='utf8')

_player_stats = Table('player_stats',
                      _metadata,
                      Column('name',
                             String(50),  # XXX: is this long enough?
                             primary_key=True),
                      Column('stats',
                             _JsonEncodedDict(100000),
                             nullable=False),
                      mysql_engine='InnoDB',
                      mysql_charset='utf8')

_global_stats = Table('global_stats',
                      _metadata,
                      Column('key',
                             String(100),
                             primary_key=True),
                      Column('data',
                             _JsonEncodedDict(100000),
                             nullable=False),
                      mysql_engine='InnoDB',
                      mysql_charset='utf8')

_engine = sqlalchemy.create_engine(DB_URI,
                                   pool_size=1,
                                   max_overflow=-1,
                                   pool_recycle=60)

if DB_URI.startswith('sqlite'):
    sqlalchemy.event.listen(_engine, 'connect', sqlite_performance_over_safety)

_metadata.create_all(_engine)


def add_game(gid, raw_data):
    """Add a game to the database."""
    conn = _engine.connect()
    try:
        name = raw_data['name']
        start = modelutils.prettycrawldate(raw_data['start'],
                                           return_datetime=True)
        end = modelutils.prettycrawldate(raw_data['end'], return_datetime=True)
        type(start)
        runes = raw_data['urune'] if 'urune' in raw_data else 0
        conn.execute(_games.insert(),
                     gid=gid,
                     name=name,
                     start=start,
                     end=end,
                     runes=runes,
                     raw_data=raw_data)
    except (sqlalchemy.exc.IntegrityError, _mysql_exceptions.IntegrityError, _mysql_exceptions.OperationalError):
        raise DatabaseError("Duplicate game %s, ignoring." % gid)


def get_logfile_pos(logfile):
    """Get the number of lines we've already processed."""
    conn = _engine.connect()
    s = _logfile_progress.select().where(_logfile_progress.c.logfile ==
                                         logfile)
    row = conn.execute(s).fetchone()
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
    conn = _engine.connect()
    try:
        conn.execute(_logfile_progress.insert(),
                     logfile=logfile,
                     lines_parsed=pos)
    except sqlalchemy.exc.IntegrityError:
        conn.execute(_logfile_progress.update().where(
            _logfile_progress.c.logfile == logfile).values(lines_parsed=pos))


def players():
    """Return list of all players.

    XXX should be at least memoised if not outright replaced with something
    saner.
    """
    conn = _engine.connect()
    return [i.name for i in get_all_player_stats()]


def get_all_player_stats():
    """Return all rows in player_stats table.

    XXX should be at least memoised if not outright replaced with something
    saner.
    """
    conn = _engine.connect()
    s = _player_stats.select()
    return conn.execute(s).fetchall()


def delete_all_player_stats():
    """Deletes all player stats."""
    conn = _engine.connect()
    conn.execute(_player_stats.delete())


def delete_player_stats(name):
    """Deletes a player's stats."""
    conn = _engine.connect()
    conn.execute(_player_stats.delete().where(_player_stats.c.name == name))


def get_player_stats(name):
    """Return a dict of the player's current stats.

    If the player doesn't exist, None is returned.
    """
    conn = _engine.connect()
    s = _player_stats.select().where(_player_stats.c.name == name)
    result = conn.execute(s).fetchone()
    if result:
        score = result[1]
    else:
        score = None
    return score


def set_player_stats(name, stats):
    """Write player's stats to the database.

    XXX this function is the slowest part of scoring.py.
    """
    conn = _engine.connect()
    # print("Saving scoring data for", player)
    try:
        conn.execute(_player_stats.insert(), name=name, stats=stats)
    except sqlalchemy.exc.IntegrityError:
        conn.execute(_player_stats.update().where(_player_stats.c.name ==
                                                  name).values(stats=stats))


def get_all_games(scored=None):
    """Return all games.

    If scored is not none, only return games who match bool(scored).
    Games are ordered by end datetime.

    Note: Uses a lot of RAM if there are a lot of games.
    XXX fix this.
    """
    conn = _engine.connect()
    s = _games.select()
    if scored is not None:
        s = s.where(_games.c.scored == bool(scored)).order_by(_games.c.end.asc(
        ))
    return conn.execute(s).fetchall()


def mark_game_scored(gid):
    """Mark a game as being scored."""
    conn = _engine.connect()
    s = _games.update().where(_games.c.gid == gid).values(scored=True)
    conn.execute(s)


def unscore_all_games():
    """Marks all games as being unscored."""
    conn = _engine.connect()
    conn.execute(_games.update().values(scored=False))


def unscore_all_games_of_player(name):
    """Marks all games by a player as being unscored."""
    conn = _engine.connect()
    conn.execute(_games.update().where(_games.c.name == name).values(scored=
                                                                     False))


def set_global_stat(key, data):
    """Set global stat data."""
    conn = _engine.connect()
    try:
        conn.execute(_global_stats.insert(), key=key, data=data)
    except sqlalchemy.exc.IntegrityError:
        conn.execute(_global_stats.update().where(_global_stats.c.key ==
                                                  key).values(data=data))


def get_global_stat(key):
    """Get global score data."""
    conn = _engine.connect()
    s = _global_stats.select().where(_global_stats.c.key == key)
    val = conn.execute(s).fetchone()
    if val is not None:
        return val[1]
    else:
        return None


def get_all_global_stats():
    """Get all global score data."""
    conn = _engine.connect()
    scores = {}
    s = _global_stats.select()
    for row in conn.execute(s).fetchall():
        scores[row[0]] = row[1]
    return scores


def delete_all_global_stats():
    """Deletes all global stats."""
    conn = _engine.connect()
    conn.execute(_global_stats.delete())
