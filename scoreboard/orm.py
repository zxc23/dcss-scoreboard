"""Basic data model."""

import sqlite3  # for typing
import os

import characteristic

import sqlalchemy
from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool
import sqlalchemy.ext.declarative.api

from . import model

Base = declarative_base()  # type: sqlalchemy.ext.declarative.api.DeclarativeMeta

Session = None


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Server(Base):
    """A DCSS server -- a source of logfiles/milestones.

    Columns:
        name: Server's short name (eg CAO, CPO).
    """

    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(4), nullable=False, index=True, unique=True)  # type: str


# Many-to-many mapping of players to achivements
AwardedAchievements = Table(
    "awarded_achievements",
    Base.metadata,
    Column("player_id", Integer, ForeignKey("players.id"), nullable=False),
    Column("achievement_id", Integer, ForeignKey("achievements.id"), nullable=False),
)


@characteristic.with_repr(["name", "server"])  # pylint: disable=too-few-public-methods
class Account(Base):
    """An account -- a single username on a single server.

    Columns:
        name: name of the account on the server
        blacklisted: if the account has been blacklisted. Accounts started as
            streak griefers/etc are blacklisted.
    """

    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True)  # type: str
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)  # type: int
    server = relationship("Server")
    blacklisted = Column(Boolean, nullable=False, default=False)  # type: bool
    player_id = Column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )  # type: int
    player = relationship("Player", back_populates="accounts")

    @property
    def canonical_name(self) -> str:
        """Canonical name.

        Crawl names are case-insensitive, we preserve the account's
        preferred capitalisation, but store them uniquely using the canonical
        name.
        """
        return self.name.lower()

    __table_args__ = (UniqueConstraint("name", "server_id", name="name-server_id"),)


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Player(Base):
    """A player -- a collection of accounts with shared metadata.

    Columns:
        name: Player's name. For now, this is the same as the accounts that
            make up the player. In future, it could be changed so that
            differently-named accounts can make up a single player (eg
            Sequell nick mapping).
    """

    __tablename__ = "players"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), unique=True, nullable=False)  # type: str
    page_updated = Column(DateTime, nullable=False, index=True)  # type: DateTime
    accounts = relationship("Account", back_populates="player")  # type: list
    achievements = relationship(
        "Achievement", secondary=AwardedAchievements, back_populates="players"
    )

    streak = relationship("Streak", uselist=False, back_populates="player")

    @property
    def url_name(self):
        return self.name.lower()


@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Species(Base):
    """A DCSS player species.

    Columns:
        short: short species name, eg 'HO', 'Mi'.
        name: long species name, eg 'Hill Orc', 'Minotaur'.
        playable: if the species is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "species"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(15), nullable=False, unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Background(Base):
    """A DCSS player background.

    Columns:
        short: short background name, eg 'En', 'Be'.
        name: long background name, eg 'Enchanter', 'Berserker'.
        playable: if the background is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "backgrounds"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class God(Base):
    """A DCSS god.

    Columns:
        name: full god name, eg 'Nemelex Xobeh', 'Trog'.
        playable: if the god is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "gods"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["v"])  # pylint: disable=too-few-public-methods
class Version(Base):
    """A DCSS version.

    Columns:
        v: version string, eg '0.17', '0.18'.
    """

    __tablename__ = "versions"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    v = Column(String(10), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Branch(Base):
    """A DCSS Branch (Dungeon, Lair, etc).

    Columns:
        short: short code, eg 'D', 'Wizlab'.
        name: full name, eg 'Dungeon', 'Wizard\'s Laboratory'.
        multilevel: Is the branch multi-level? Note: Pandemonium is not
            considered multilevel, since its levels are not numbered ingame.
        playable: Is it playable in the current version?
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(10), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    multilevel = Column(Boolean, nullable=False)  # type: bool
    playable = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["branch", "level"])  # pylint: disable=too-few-public-methods
class Place(Base):
    """A DCSS Place (D:8, Pan:1, etc).

    Note that single-level branches have a single place with level=1 (eg
        Temple:1, Pan:1).
    """

    __tablename__ = "places"
    id = Column("id", Integer, primary_key=True, nullable=False)  # type: int
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)  # type: int
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

    __table_args__ = (UniqueConstraint("branch_id", "level", name="branch_id-level"),)


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Ktyp(Base):
    """A DCSS ktyp (mon, beam, etc)."""

    __tablename__ = "ktyps"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["player", "id"])  # pylint: disable=too-few-public-methods
class Streak(Base):
    """A streak of wins.

    Each player can have one active streak at a time, this is enforced with a
    partial index (note: only supported in postgresql).

    Columns:
        active: is the streak currently active?
    """

    __tablename__ = "streaks"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    active = Column(Boolean, nullable=False, index=True)  # type: bool

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)  # type: int
    player = relationship("Player", back_populates="streak")

    games = relationship("Game", order_by="Game.start")

    __table_args__ = (
        Index(
            "one_active_streak_per_player",
            player_id,
            postgresql_where=active == sqlalchemy.true(),
            sqlite_where=active == sqlalchemy.true(),
        ),
    )


@characteristic.with_repr(["gid"])  # pylint: disable=too-few-public-methods
class Game(Base):
    """A single DCSS game.

    Columns (most are self-explanatory):
        gid: unique id for the game, comprised of "name:server:start". For
            compatibility with sequell.
        xl
        tmsg: description of game end
        turn
        dur
        runes
        score
        start: start time for the game (in UTC)
        end: end time for the game (in UTC)
        potions_use:
        scrolls_used
        scored: Has the game been procssed by scoring yet?
    """

    __tablename__ = "games"
    gid = Column(String(50), primary_key=True, nullable=False)  # type: str

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)  # type: int
    account = relationship("Account")

    # Denormalised data. Set on game record insertion
    player_id = Column(Integer, nullable=False, index=True)  # type: int

    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)  # type: int
    version = relationship("Version")

    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)  # type: int
    species = relationship("Species")

    background_id = Column(
        Integer, ForeignKey("backgrounds.id"), nullable=False
    )  # type: int
    background = relationship("Background")

    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)  # type: int
    place = relationship("Place")

    god_id = Column(Integer, ForeignKey("gods.id"), nullable=False)  # type: int
    god = relationship("God")

    xl = Column(Integer, nullable=False)  # type: int
    dam = Column(Integer, nullable=False)  # type: int
    sdam = Column(Integer, nullable=False)  # type: int
    tdam = Column(Integer, nullable=False)  # type: int
    tmsg = Column(String(1000), nullable=False)  # type: str
    turn = Column(Integer, nullable=False)  # type: int
    dur = Column(Integer, nullable=False)  # type: int
    runes = Column(Integer, nullable=False)  # type: int
    score = Column(Integer, nullable=False, index=True)  # type: int
    start = Column(DateTime, nullable=False, index=True)  # type: DateTime
    end = Column(DateTime, nullable=False, index=True)  # type: DateTime
    potions_used = Column(Integer, nullable=False)  # type: int
    scrolls_used = Column(Integer, nullable=False)  # type: int

    ktyp_id = Column(Integer, ForeignKey("ktyps.id"), nullable=False)  # type: int
    ktyp = relationship("Ktyp")

    scored = Column(Boolean, default=False, nullable=False, index=True)  # type: bool

    streak_id = Column(Integer, ForeignKey("streaks.id"), index=True)  # type: int
    streak = relationship("Streak")

    __table_args__ = (
        # Used to find various highscores in model
        # XXX: these indexes should have a sqlite_where=ktyp_id == 'winning'
        # But these indexes can then only be added after the 'winning' ktyp is
        # added.... chicken & egg.
        Index("species_highscore_index", species_id, score),
        Index("background_highscore_index", background_id, score),
        Index("combo_highscore_index", species_id, background_id, score),
        Index("fastest_highscore_index", ktyp_id, dur),
        Index("shortest_highscore_index", ktyp_id, turn),
        # Used by scoring.score_games
        Index("unscored_games", scored, end),
        # Used by scoring.is_grief
        Index("first_game_index", account_id, end),
    )

    @property
    def player(self) -> Player:
        """Convenience shortcut."""
        return self.account.player

    @property
    def won(self) -> bool:
        """Was this game won."""
        return self.ktyp.name == "winning"

    @property
    def quit(self) -> bool:
        """Was this game quit."""
        return self.ktyp.name == "quitting"

    @property
    def boring(self) -> bool:
        """Was this game was quit, left, or wizmoded."""
        return self.ktyp.name in ("quitting", "leaving", "wizmode")

    @property
    def char(self) -> str:
        """Character code eg 'MiFi'."""
        return "{}{}".format(self.species.short, self.background.short)

    @property
    def pretty_tmsg(self) -> str:
        """Pretty tmsg, more suitable for scoreboard display."""
        msg = self.tmsg
        if not msg:
            return msg
        if msg == "escaped with the Orb":
            msg += "!"
        # We don't use str.capitalize because it lower-cases all letters but
        # the first. We just want to specifically capitalise the first letter.
        return msg[0].upper() + msg[1:]

    def as_dict(self) -> dict:
        """Convert to a dict, for public consumption."""
        return {
            "gid": self.gid,
            "account_name": self.account.name,
            "player_name": self.player.name,
            "server_name": self.account.server.name,
            "version": self.version.v,
            "species": self.species.name,
            "background": self.background.name,
            "char": self.char,
            "place": self.place.as_string,
            "god": self.god.name,
            "xl": self.xl,
            "tmsg": self.tmsg,
            "turns": self.turn,
            "dur": self.dur,
            "runes": self.runes,
            "score": self.score,
            "start": self.start.timestamp(),
            "end": self.end.timestamp(),
        }


@characteristic.with_repr(["logfile"])  # pylint: disable=too-few-public-methods
class LogfileProgress(Base):
    """Logfile import progress.

    Columns:
        source_url: logfile source url
        current_key: the key of the next logfile event to import.
    """

    __tablename__ = "logfile_progress"
    source_url = Column(String(100), primary_key=True)  # type: str
    current_key = Column(Integer, default=0, nullable=False)  # type: int


@characteristic.with_repr(["key"])  # pylint: disable=too-few-public-methods
class Achievement(Base):
    """Achievements.

    Column:
        key: short, human-readable key to refer to the achievement, eg
            'polytheist'
        name: long, human-readable name, eg 'Polytheist'
        description: human-readable description of the achievement. This should
            be written as a directive to the reader, eg 'Win a game with each
            God'
    """

    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)  # type: int
    key = Column(String(50), nullable=False, index=True)  # type: str
    name = Column(String(50), nullable=False, index=True)  # type: str
    description = Column(String(200), nullable=False)  # type: str
    players = relationship(
        "Player", secondary=AwardedAchievements, back_populates="achievements"
    )


def sqlite_performance_over_safety(
    dbapi_con: sqlite3.Connection,
    con_record: sqlalchemy.pool._ConnectionRecord,  # pylint: disable=protected-access
) -> None:
    """Significantly speeds up inserts but will break on crash."""
    con_record  # pylint: disable=pointless-statement
    dbapi_con.execute("PRAGMA journal_mode = MEMORY")
    dbapi_con.execute("PRAGMA synchronous = OFF")


def setup_database(*, database: str, path: str) -> None:
    """Set up the database and create the master sessionmaker."""
    if database == "sqlite":
        db_uri = "sqlite:///{database_path}".format(database_path=path)
    elif database == "postgres":
        db_uri = "postgresql+psycopg2://{u}:{p}@{h}/scoreboard".format(
            u=os.environ['DB_USERNAME'],
            p=os.environ['DB_PASSWORD'],
            h=os.environ['DB_HOST'],
        )
    else:
        raise ValueError("Unknown database type!")
    print("Connecting to {}".format(db_uri))
    engine_opts = {"poolclass": sqlalchemy.pool.NullPool}
    engine = sqlalchemy.create_engine(db_uri, **engine_opts)

    if db_uri.startswith("sqlite"):
        sqlalchemy.event.listen(engine, "connect", sqlite_performance_over_safety)

    Base.metadata.create_all(engine)

    # Create the global session manager
    global Session  # pylint: disable=global-statement
    Session = sessionmaker(bind=engine)

    sess = Session()

    model.setup_species(sess)
    model.setup_backgrounds(sess)
    model.setup_gods(sess)
    model.setup_branches(sess)
    model.setup_achievements(sess)
    model.setup_ktyps(sess)


def get_session() -> sqlalchemy.orm.session.Session:
    """Create a new database session."""
    if Session is None:
        raise Exception("Database hasn't been initialised, run setup_database() first!")
    return Session()
