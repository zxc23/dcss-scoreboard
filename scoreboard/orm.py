"""Basic data model."""

import characteristic

from sqlalchemy import Column, String, \
                       Integer, Boolean, DateTime, \
                       ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


@characteristic.with_repr(["name"])
class Server(Base):
    """A DCSS server -- a source of logfiles/milestones."""

    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(4), nullable=False, index=True, unique=True)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["name", "server"])
class Player(Base):
    """A player -- a single account on a server."""

    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(20), nullable=False, index=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    server = relationship("Server")
    blacklisted = Column(Boolean, nullable=False, default=False)

    __table_args__ = (UniqueConstraint(
        'name', 'server_id', name='name-server_id'),
                      {'mysql_engine': 'InnoDB',
                       'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["short"])
class Species(Base):
    """A DCSS player species."""

    __tablename__ = 'species'
    id = Column(Integer, primary_key=True, nullable=False)
    short = Column(String(2), nullable=False, index=True, unique=True)
    full = Column(String(15), nullable=False, unique=True)
    playable = Column(Boolean, nullable=False)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["short"])
class Background(Base):
    """A DCSS player background."""

    __tablename__ = 'backgrounds'
    id = Column(Integer, primary_key=True, nullable=False)
    short = Column(String(2), nullable=False, index=True, unique=True)
    full = Column(String(20), nullable=False, index=True, unique=True)
    playable = Column(Boolean, nullable=False)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["name"])
class God(Base):
    """A DCSS god."""

    __tablename__ = 'gods'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(20), nullable=False, index=True, unique=True)
    playable = Column(Boolean, nullable=False)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["v"])
class Version(Base):
    """A DCSS version."""

    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True, nullable=False)
    v = Column(String(10), nullable=False, index=True, unique=True)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["short"])
class Branch(Base):
    """A DCSS Branch (Dungeon, Lair, etc)."""

    __tablename__ = 'branches'
    id = Column(Integer, primary_key=True, nullable=False)
    short = Column(String(10), nullable=False, index=True, unique=True)
    full = Column(String(20), nullable=False, index=True, unique=True)
    playable = Column(Boolean, nullable=False)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["branch", "level"])
class Place(Base):
    """A DCSS Place (D:8, Pan:1, etc).

    Note that single-level branches have a level of 1.
    """

    __tablename__ = 'places'
    id = Column('id', Integer, primary_key=True, nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    branch = relationship("Branch")
    level = Column(Integer, nullable=False, index=True)

    __table_args__ = (UniqueConstraint(
        'branch_id', 'level', name='branch_id-level'),
                      {'mysql_engine': 'InnoDB',
                       'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["gid"])
class Game(Base):
    """A single DCSS game."""

    __tablename__ = 'games'
    gid = Column(String(50), primary_key=True, nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player = relationship("Player")

    version_id = Column(Integer, ForeignKey('versions.id'))
    version = relationship("Version")

    species_id = Column(Integer, ForeignKey('species.id'))
    species = relationship("Species")

    background_id = Column(Integer, ForeignKey('backgrounds.id'))
    background = relationship("Background")

    place_id = Column(Integer, ForeignKey('places.id'))
    place = relationship("Place")

    # god_id = Column(Integer, ForeignKey('gods.id'))
    # god = relationship("God")

    xl = Column(Integer, nullable=False)
    tmsg = Column(String(1000), nullable=False)
    turn = Column(Integer, nullable=False)
    dur = Column(Integer, nullable=False)
    runes = Column(Integer, nullable=False)
    sc = Column(Integer, nullable=False, index=True)
    start = Column(DateTime, nullable=False, index=True)
    end = Column(DateTime, nullable=False, index=True)
    ktyp = Column(String(50), nullable=False, index=True)

    scored = Column(Boolean, default=False, index=True)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )


@characteristic.with_repr(["logfile"])
class LogfileProgress(Base):
    """Logfile import progress."""

    __tablename__ = 'logfile_progress'
    name = Column(String(100), primary_key=True)
    bytes_parsed = Column(Integer, nullable=False, default=0)

    __table_args__ = ({'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}, )
