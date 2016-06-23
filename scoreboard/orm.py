"""Basic data model."""

from typing import Optional

import characteristic

import sqlalchemy
from sqlalchemy import Table, Column, String, Integer, Boolean, DateTime, \
                       ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool

from . import model

Base = declarative_base()

Session = None


@characteristic.with_repr(["name"])
class Server(Base):
    """A DCSS server -- a source of logfiles/milestones."""

    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(4), nullable=False, index=True,
                  unique=True)  # type: str


AwardedAchievements = Table('awarded_achievements',
                            Base.metadata,
                            Column('player_id',
                                   Integer,
                                   ForeignKey('players.id'),
                                   nullable=False),
                            Column('achievement_id',
                                   Integer,
                                   ForeignKey('achievements.id'),
                                   nullable=False), )


@characteristic.with_repr(["name", "server"])
class Account(Base):
    """An account -- a single username on a single server."""

    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True)  # type: str
    server_id = Column(Integer, ForeignKey('servers.id'),
                       nullable=False)  # type: int
    server = relationship("Server")
    blacklisted = Column(Boolean, nullable=False, default=False)  # type: bool
    player_id = Column(Integer, ForeignKey('players.id'),
                       nullable=False)  # type: int
    player = relationship("Player")

    @property
    def canonical_name(self) -> str:
        """Canonical name.

        Crawl names are case-insensitive, we preserve the account's
        preferred capitalisation, but store them uniquely using the canonical
        name.
        """
        return self.name.lower()

    __table_args__ = (UniqueConstraint('name',
                                       'server_id',
                                       name='name-server_id'),
                      )


@characteristic.with_repr(["name"])
class Player(Base):
    """A player -- a collection of accounts with shared metadata."""

    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), unique=True, nullable=False)  # type: str
    achievements = relationship("Achievement",
                                secondary=AwardedAchievements,
                                back_populates="players")

    streak = relationship("Streak", uselist=False, back_populates="player")


@characteristic.with_repr(["short"])
class Species(Base):
    """A DCSS player species."""

    __tablename__ = 'species'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True,
                   unique=True)  # type: str
    name = Column(String(15), nullable=False, unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["short"])
class Background(Base):
    """A DCSS player background."""

    __tablename__ = 'backgrounds'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True,
                   unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True,
                  unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["name"])
class God(Base):
    """A DCSS god."""

    __tablename__ = 'gods'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["v"])
class Version(Base):
    """A DCSS version."""

    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    v = Column(String(10), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["short"])
class Branch(Base):
    """A DCSS Branch (Dungeon, Lair, etc)."""

    __tablename__ = 'branches'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(10), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    multilevel = Column(Boolean, nullable=False)  # type: bool
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["branch", "level"])
class Place(Base):
    """A DCSS Place (D:8, Pan:1, etc).

    Note that single-level branches have a level of 1.
    """

    __tablename__ = 'places'
    id = Column('id', Integer, primary_key=True, nullable=False)  # type: int
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)  # type: int
    branch = relationship("Branch")
    level = Column(Integer, nullable=False, index=True)  # type: int

    @property
    def as_string(self) -> str:
        """Return the Place with a pretty name, like D:15 or Temple."""
        # TODO: should specify name in 'normal' form eg 'Gehenna' etc
        if self.branch.multilevel:
            return "%s:%s" % (self.branch.short, self.level)
        else:
            return "%s" % self.branch.short

    __table_args__ = (UniqueConstraint('branch_id',
                                       'level',
                                       name='branch_id-level'),
                      )


@characteristic.with_repr(["name"])
class Ktyp(Base):
    """A DCSS ktyp (mon, beam, etc)."""

    __tablename__ = 'ktyps'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["player", "id"])
class Streak(Base):
    """A streak of wins.

    Each player can have one active streak at a time, this is enforced with a
    partial index (note: not supported in MySQL).
    """

    __tablename__ = 'streaks'
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    active = Column(Boolean, nullable=False, index=True)  # type: bool

    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)  # type: int
    player = relationship("Player", back_populates="streak")

    games = relationship("Game")

    __table_args__ = (
        Index('one_active_streak_per_player',
              player_id,
              postgresql_where=active == True),
        )


@characteristic.with_repr(["gid"])
class Game(Base):
    """A single DCSS game."""

    __tablename__ = 'games'
    gid = Column(String(50), primary_key=True, nullable=False)  # type: str

    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)  # type: int
    account = relationship("Account")

    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)  # type: int
    version = relationship("Version")

    species_id = Column(Integer, ForeignKey('species.id'), nullable=False)  # type: int
    species = relationship("Species")

    background_id = Column(Integer,
                           ForeignKey('backgrounds.id'),
                           nullable=False)  # type: int
    background = relationship("Background")

    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)  # type: int
    place = relationship("Place")

    god_id = Column(Integer, ForeignKey('gods.id'), nullable=False)  # type: int
    god = relationship("God")

    xl = Column(Integer, nullable=False)  # type: int
    tmsg = Column(String(1000), nullable=False)  # type: str
    turn = Column(Integer, nullable=False)  # type: int
    dur = Column(Integer, nullable=False)  # type: int
    runes = Column(Integer, nullable=False)  # type: int
    score = Column(Integer, nullable=False, index=True)  # type: int
    start = Column(DateTime, nullable=False, index=True)  # type: datetime.datetime
    end = Column(DateTime, nullable=False, index=True)  # type: datetime.datetime
    potions_used = Column(Integer, nullable=False)  # type: int
    scrolls_used = Column(Integer, nullable=False)  # type: int

    ktyp_id = Column(Integer, ForeignKey('ktyps.id'), nullable=False)  # type: int
    ktyp = relationship("Ktyp")

    scored = Column(Boolean, default=False, nullable=False, index=True)  # type: bool

    streak_id = Column(Integer, ForeignKey('streaks.id'))  # type: int
    streak = relationship("Streak")

    @property
    def player(self) -> Player:
        """Convenience shortcut to access player"""
        return self.account.player

    @property
    def won(self) -> bool:
        """Was this game won?"""
        return self.ktyp.name == 'winning'

    @property
    def quit(self) -> bool:
        """Was this game quit?"""
        return self.ktyp.name == 'quitting'

    @property
    def char(self) -> str:
        """Four letter character code eg 'MiFi'."""
        return '{}{}'.format(self.species.short, self.background.short)


@characteristic.with_repr(["logfile"])
class LogfileProgress(Base):
    """Logfile import progress."""

    __tablename__ = 'logfile_progress'
    name = Column(String(100), primary_key=True)  # type: str
    bytes_parsed = Column(Integer, nullable=False, default=0)  # type: int


@characteristic.with_repr(["id"])
class Achievement(Base):
    """Achievements."""

    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)  # type: int
    key = Column(String(50), nullable=False)  # type: str
    name = Column(String(50), nullable=False)  # type: str
    description = Column(String(200), nullable=False)  # type: str
    players = relationship("Player",
                           secondary=AwardedAchievements,
                           back_populates="achievements")


def sqlite_performance_over_safety(dbapi_con, con_record) -> None:
    """Significantly speeds up inserts but will break on crash."""
    dbapi_con.execute('PRAGMA journal_mode = MEMORY')
    dbapi_con.execute('PRAGMA synchronous = OFF')


def setup_database(database: str, credentials: Optional[str]=None) -> None:
    """Set up the database and create the master sessionmaker."""
    if database == 'sqlite':
        db_uri = 'sqlite:///database.db3'
    elif database == 'postgres':
        db_uri = 'postgresql+psycopg2://{creds}localhost/scoreboard'
        if credentials:
            db_uri = db_uri.format(creds='%s@' % credentials)
        else:
            db_uri = db_uri.format(creds='')
    else:
        raise ValueError("Unknown database type!")
    engine_opts = {'poolclass': sqlalchemy.pool.NullPool}
    engine = sqlalchemy.create_engine(db_uri, **engine_opts)

    if db_uri.startswith('sqlite'):
        sqlalchemy.event.listen(engine, 'connect',
                                sqlite_performance_over_safety)

    Base.metadata.create_all(engine)

    # Create the global session manager
    global Session
    Session = sessionmaker(bind=engine)

    sess = Session()

    model.setup_servers(sess)
    model.setup_species(sess)
    model.setup_backgrounds(sess)
    model.setup_gods(sess)
    model.setup_branches(sess)
    model.setup_achievements(sess)
    model.setup_ktyps(sess)


def get_session():
    """Create a new database session."""
    if Session is None:
        raise Exception("Database hasn't been initialised, run setup_database() first!")
    return Session()
