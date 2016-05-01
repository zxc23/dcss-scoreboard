"""Defines the database models for this module."""

import json
import collections
import datetime
import os

import pylru
import sqlalchemy.ext.mutable
from sqlalchemy import TypeDecorator, MetaData, Table, Column, String, \
                       Integer, Boolean, DateTime, LargeBinary, Index
from sqlalchemy import desc, asc, select, func, column

from . import modelutils
from . import constants as const

GAME_CACHE = pylru.lrucache(1000)


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
    global DB_URI
    if backend == 'sqlite':
        DB_URI = 'sqlite:///database.db'
        ENGINE_OPTS = {}
    elif backend == 'mysql':
        auth = '' if 'DB_USER' not in os.environ else '%s:%s@' % (
            os.environ.get('DB_USER'), os.environ.get('DB_PASS'))
        DB_URI = 'mysql://%slocalhost/dcss_scoreboard' % auth
        ENGINE_OPTS = {'pool_size': 1, 'max_overflow': -1, 'pool_recycle': 60}
    else:
        raise RuntimeError("Unknown database backend %s" % backend)
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
                   Column('char', String(4), nullable=False, index=True),
                   Column('rc', String(2), nullable=False, index=True),
                   Column('bg', String(2), nullable=False, index=True),
                   Column('place', String(12), nullable=False),
                   Column('xl', Integer, nullable=False),
                   Column('tmsg', String(1000), nullable=False),
                   Column('turn', Integer, nullable=False),
                   Column('dur', Integer, nullable=False),
                   Column('runes', Integer, nullable=False),
                   Column('sc', Integer, nullable=False, index=True),
                   Column('god', String(20), nullable=False, index=True),
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

    Index('ix_games_rc_sc', _games.c.rc, _games.c.sc)
    Index('ix_games_bg_sc', _games.c.bg, _games.c.sc)
    Index('ix_games_char_sc', _games.c.char, _games.c.sc)
    Index('ix_games_god_sc', _games.c.god, _games.c.sc)

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

    global _blacklisted_players
    _blacklisted_players = Table('blacklisted_players',
                                 _metadata,
                                 Column('name',
                                        String(50),
                                        primary_key=True,
                                        nullable=False),
                                 Column('src',
                                        String(4),
                                        primary_key=True,
                                        nullable=False),
                                 mysql_engine='InnoDB',
                                 mysql_charset='utf8')

    global _player_stats
    _player_stats = Table('player_stats',
                          _metadata,
                          Column('name',
                                 String(50),  # XXX: is this long enough?
                                 primary_key=True,
                                 nullable=False),
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
                                 primary_key=True,
                                 nullable=False),
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
    elif DB_URI.startswith('mysql'):
        version = _engine.execute('select VERSION()').fetchone()[0]
        # We split on '-' to get rid of OS-specific junk like:
        # 5.5.49-0ubuntu0.14.04.1
        _engine.MYSQL_VERSION = [int(v)
                                 for v in version.split('-')[0].split('.')]
        assert (_engine.MYSQL_VERSION[0] == 5)

    _metadata.create_all(_engine)


def add_game(gid, raw_data):
    """Normalise and add a game to the database."""
    raw_data['god'] = const.GOD_NAME_FIXUPS.get(raw_data['god'],
                                                raw_data['god'])
    raw_data['original_race'] = raw_data['race']
    raw_data['race'] = const.RACE_NAME_FIXUPS.get(raw_data['race'],
                                                  raw_data['race'])
    conn = _engine.connect()
    try:
        conn.execute(
            _games.insert(),
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
    except sqlalchemy.exc.IntegrityError as e:
        if e.orig.args[0] == 1062:  # duplicate entry for private key
            raise DatabaseError("Gid %s already exists in the database." % gid)


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
    """Delete all player stats."""
    conn = _engine.connect()
    conn.execute(_player_stats.delete())


def delete_player_stats(name):
    """Delete a player's stats."""
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
    """Return the first game of a player."""
    conn = _engine.connect()
    s = _games.select().where(_games.c.name == name).order_by(asc(
        'start')).limit(1)
    if src is not None:
        s = s.where(_games.c.src == src)
    return conn.execute(s).fetchone()


def all_games(scored=None, limit=0):
    """Return all games.

    If scored is not none, only return games who match bool(scored).
    Return (up to) limit rows (0 = all rows).
    Games are ordered by end datetime.
    """
    conn = _engine.connect()
    s = _games.select()
    if scored is not None:
        s = s.where(_games.c.scored == bool(scored)).order_by(asc('end'))
    if limit:
        s = s.limit(limit)
    return conn.execute(s).fetchall()


def mark_game_scored(gid):
    """Mark a game as being scored."""
    conn = _engine.connect()
    s = _games.update().where(_games.c.gid == gid).values(scored=True)
    conn.execute(s)


def unscore_all_games():
    """Mark all games as being unscored."""
    conn = _engine.connect()
    conn.execute(_games.update().values(scored=False))


def unscore_all_games_of_player(name):
    """Mark all games by a player as being unscored."""
    conn = _engine.connect()
    q = _games.update().where(_games.c.name == name).values(scored=False)
    conn.execute(q)


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
        raise TypeError("Must pass in string, `%s` is type %s" %
                        (repr(gid), type(gid)))
    if gid in GAME_CACHE:
        return GAME_CACHE[gid]
    conn = _engine.connect()
    game = conn.execute(_games.select().where(_games.c.gid == gid)).fetchone()
    GAME_CACHE[gid] = game
    return game


def recent_games(wins=False,
                 player=None,
                 num=const.PLAYER_TABLE_LENGTH,
                 reverse=False):
    """Return recent games.

    Parameters:
        wins (bool) Only return wins
        player (str) Only for this player, None for all
        num (int) Number of rows to return, None for all
        reverse (bool) Order in least -> most recent if True

    Returns recent games as a list of Games.
    """
    conn = _engine.connect()
    query = _games.select()
    if wins:
        query = query.where(_games.c.ktyp == 'winning')
    if player is not None:
        query = query.where(_games.c.name == player)
    if num is not None:
        query = query.limit(num)
    query = query.order_by(desc("end"))

    rows = conn.execute(query).fetchall()
    if reverse:
        rows = rows[::-1]
    return rows


def games_by_type(player, col, eligible, winning=True):
    """Find the count of games for a player grouped by values of col."""
    conn = _engine.connect()
    count = sqlalchemy.sql.functions.count()
    query = select([column(col), count]).group_by(col)
    query = query.where(_games.c.name == player)
    if winning:
        query = query.where(_games.c.ktyp == 'winning')
    query = query.group_by(col)
    print(query.compile(compile_kwargs={"literal_binds": True}))
    return {i[0]: i[1]
            for i in conn.execute(query).fetchall() if i[0] in eligible}


def add_player_to_blacklist(name, src):
    """Add a player to the blacklist."""
    conn = _engine.connect()
    conn.execute(_blacklisted_players.insert(), name=name, src=src)


def remove_player_from_blacklist(name, src):
    """Remove a player from the blacklist."""
    conn = _engine.connect()
    table = _blacklisted_players
    s = table.delete().where(table.c.name == name).where(table.c.src == src)
    conn.execute(s)


def player_in_blacklist(name, src):
    """Return True if a player is on the blacklist."""
    conn = _engine.connect()
    table = _blacklisted_players
    s = table.select().where(table.c.name == name).where(table.c.src == src)
    return conn.execute(s).fetchone() is True


def all_blacklisted_players():
    """Return all blacklisted player-src combinations."""
    conn = _engine.connect()
    return conn.execute(_blacklisted_players.select()).fetchall()


def shortest_wins(n=const.GLOBAL_TABLE_LENGTH):
    """Return the n shortest wins by turncount."""
    conn = _engine.connect()
    s = _games.select().where(_games.c.ktyp == 'winning').order_by(asc(
        'turn')).limit(n)
    return conn.execute(s).fetchall()


def fastest_wins(n=const.GLOBAL_TABLE_LENGTH):
    """Return the n fastest wins by duration."""
    conn = _engine.connect()
    s = _games.select().where(_games.c.ktyp == 'winning').order_by(asc(
        'dur')).limit(n)
    return conn.execute(s).fetchall()


def highscores(n=const.GLOBAL_TABLE_LENGTH):
    """Return the n highest scoring games."""
    conn = _engine.connect()
    s = _games.select().order_by(desc('sc')).limit(n)
    return conn.execute(s).fetchall()


def _highscores(col, values):
    conn = _engine.connect()
    cols = [_games.c.gid, _games.c.sc]
    # For info on this mysql 5.7+ workaround, see:
    # https://dev.mysql.com/doc/refman/5.7/en/group-by-handling.html
    # XXX should rewrite the query so it doesn't require this workaround.
    if DB_URI.startswith('mysql') and _engine.MYSQL_VERSION[1] >= 7:
        cols[0] = func.ANY_VALUE(cols[0])
    s = select(cols).order_by(desc(_games.c.sc)).limit(1)

    result = []
    for val in values:
        q = s.where(col == val)
        g = conn.execute(q).fetchone()
        if g:
            result.append(game(g[0]))

    return result


def race_highscores():
    """Return the highest scoring game for each race."""
    return _highscores(_games.c.rc, const.PLAYABLE_RACES)


def role_highscores():
    """Return the highest scoring game for each role."""
    return _highscores(_games.c.bg, const.PLAYABLE_ROLES)


def god_highscores():
    """Return the highest scoring game for each god."""
    return _highscores(_games.c.god, const.PLAYABLE_GODS)


def combo_highscores():
    """Return the highest scoring game for each combo."""
    return _highscores(_games.c.char, const.PLAYABLE_COMBOS)
