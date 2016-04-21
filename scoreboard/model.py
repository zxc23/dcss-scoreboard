"""Defines the database models for this module."""

import json
import collections
import datetime

import pylru
import sqlalchemy.ext.mutable
from sqlalchemy import TypeDecorator, MetaData, Table, Column, String, Integer, Boolean, DateTime, LargeBinary
from sqlalchemy import desc, asc

from . import modelutils


GAME_CACHE = pylru.lrucache(10000)


class DatabaseError(Exception):
    """Generic error for issues with the model."""

    pass


def sqlite_performance_over_safety(dbapi_con, con_record):
    """Significantly speeds up inserts but will break on crash."""
    dbapi_con.execute('PRAGMA journal_mode = MEMORY')
    dbapi_con.execute('PRAGMA synchronous = OFF')


def json_serialise(obj):
    """Convert deques to lists.

    Used to persist deque data into JSON.
    """
    if isinstance(obj, collections.deque):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


class _JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        """Dict -> JSON String."""
        return json.dumps(value, default=json_serialise).encode()

    def process_result_value(self, value, dialect):
        """JSON String -> Dict."""
        return json.loads(value.decode())


sqlalchemy.ext.mutable.MutableDict.associate_with(_JsonEncodedDict)


def setup_database(backend):
    """Set up and initialise the database."""
    if backend == 'sqlite':
        DB_URI = 'sqlite:///database.db'
        ENGINE_OPTS = {}
    elif backend == 'mysql':
        DB_URI = 'mysql://localhost/dcss_scoreboard'
        ENGINE_OPTS = {'pool_size': 1, 'max_overflow': -1, 'pool_recycle': 60}
    else:
        raise RuntimeError("Unknown database backend %s" % db_backend)
    print("Using database %s" % DB_URI)

    _metadata = MetaData()

    global _games
    _games = Table('games',
                   _metadata,
                   Column('gid',
                          String(50),
                          primary_key=True,
                          nullable=False),
                   Column('name',
                          String(50),  # XXX: is this long enough?
                          nullable=False,
                          index=True),
                   Column('src', String(4), nullable=False),
                   Column('v', String(10), nullable=False),
                   Column('char', String(4), nullable=False),
                   Column('rc', String(2), nullable=False),
                   Column('bg', String(2), nullable=False),
                   Column('place', String(4), nullable=False),
                   Column('xl', Integer, nullable=False),
                   Column('tmsg', String(1000), nullable=False),
                   Column('turn', Integer, nullable=False),
                   Column('dur', Integer, nullable=False),
                   Column('runes', Integer, nullable=False),
                   Column('sc', Integer, nullable=False),
                   Column('god', String(20), nullable=False),
                   Column('start',
                          DateTime,
                          nullable=False,
                          index=True),
                   Column('end',
                          DateTime,
                          nullable=False,
                          index=True),
                   Column('ktyp',
                          String(50),
                          nullable=False,
                          index=True),

                   # These are columns not storing game data
                   Column('raw_data',
                          _JsonEncodedDict(10000),
                          nullable=False),
                   Column('scored',
                          Boolean,
                          default=False,
                          index=True),
                   mysql_engine='InnoDB',
                   mysql_charset='utf8')

    global _logfile_progress
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

    global _player_stats
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

    global _global_stats
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

    global _engine
    _engine = sqlalchemy.create_engine(DB_URI, **ENGINE_OPTS)

    if DB_URI.startswith('sqlite'):
        sqlalchemy.event.listen(_engine, 'connect',
                                sqlite_performance_over_safety)

    _metadata.create_all(_engine)


def add_game(gid, raw_data):
    """Add a game to the database."""
    conn = _engine.connect()
    conn.execute(_games.insert(),
                 gid=gid,
                 name=raw_data['name'],
                 src=raw_data['src'],
                 v=raw_data['v'],
                 char=raw_data['char'],
                 rc=raw_data['char'][:2],
                 bg=raw_data['char'][2:],
                 god=raw_data['god'],
                 place=raw_data['place'],
                 xl=raw_data['xl'],
                 tmsg=raw_data['tmsg'],
                 turn=raw_data['turn'],
                 dur=raw_data['dur'],
                 runes=raw_data.get('urune', 0),
                 sc=raw_data['sc'],
                 start=modelutils.crawl_date_to_datetime(raw_data['start']),
                 end=modelutils.crawl_date_to_datetime(raw_data['end']),
                 ktyp=raw_data['ktyp'],
                 raw_data=raw_data)


def logfile_pos(logfile):
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


def all_player_names():
    """Return list of all player names.

    XXX should be at least memoised if not outright replaced with something
    saner.
    """
    conn = _engine.connect()
    return [p.name for p in get_all_player_stats()]


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


def first_game(name, src=None):
    """Returns the first game of a player."""
    conn = _engine.connect()
    s = _games.select().where(_games.c.name == name).order_by(asc('start')).limit(1)
    if src is not None:
        s = s.where(_games.c.src == src)
    return conn.execute(s).fetchone()


def all_games(scored=None):
    """Return all games.

    If scored is not none, only return games who match bool(scored).
    Games are ordered by end datetime.

    Note: Uses a lot of RAM if there are a lot of games.
    XXX fix this.
    """
    conn = _engine.connect()
    s = _games.select()
    if scored is not None:
        s = s.where(_games.c.scored == bool(scored)).order_by(asc('end'))
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


def global_stat(key):
    """Get global score data."""
    conn = _engine.connect()
    s = _global_stats.select().where(_global_stats.c.key == key)
    val = conn.execute(s).fetchone()
    if val is not None:
        return val[1]
    else:
        return None


def global_stats():
    """Get all global score data."""
    conn = _engine.connect()
    scores = {}
    s = _global_stats.select()
    for row in conn.execute(s).fetchall():
        scores[row[0]] = row[1]
    return scores


def delete_all_global_stats():
    """Delete all global stats."""
    conn = _engine.connect()
    conn.execute(_global_stats.delete())


def game(gid):
    """Return game with matching gid."""
    if not isinstance(gid, str):
        raise TypeError("Must pass in string, `%s` is type %s" % (repr(gid), type(gid)))
    if gid in GAME_CACHE:
        return GAME_CACHE[gid]
    conn = _engine.connect()
    game = conn.execute(_games.select().where(
        _games.c.gid == gid)).fetchone()
    GAME_CACHE[gid] = game
    return game


def recent_games(wins=False, player=None, num=5, reverse=False):
    """Return recent games.

        Parameters:
        wins (bool) Only return wins
        player (str) Only for this player
        num (int) Number of rows to return
        reverse (bool) Order in least -> most recent if True.
    """
    conn = _engine.connect()
    query = _games.select()
    if wins:
        query = query.where(_games.c.ktyp == 'winning')
    if player is not None:
        query = query.where(_games.c.name == player)
    query = query.order_by(desc("end")).limit(num)

    rows = conn.execute(query).fetchall()
    if reverse:
        rows = rows[::-1]
    return rows
