"""Defines the database models for this module."""

import sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from . import constants as const
from .orm import Base, Server, Player, Species, Background, God, Version, \
    Branch, Place, Game, LogfileProgress
from . import modelutils


class DBError(BaseException):
    """Generic wrapper for sqlalchemy errors passed out of this module."""

    pass


def _reraise_dberror(func):
    """Re-raise errors from decorated function as DBError.

    Doesn't re-wrap DBError exceptions.
    """

    def f(*args, **kwargs):
        """Re-raise exceptions as GaiaError."""
        try:
            return func(*args, **kwargs)
        except BaseException as e:
            if isinstance(e, DBError):
                raise
            else:
                raise DBError from e

    return f


def get_server(s, name):
    """Get a server, creating it if needed."""
    server = s.query(Server).filter(Server.name == name).first()
    if server:
        return server
    else:
        server = Server(name=name)
        s.add(server)
        s.commit()
        return server


def get_player(s, name, server):
    """Get a player's object, creating them if needed.

    Note that player names are not case sensitive, so names are stored with
    their canonical capitalisation but we always compare the lowercase version.
    """
    player = s.query(Player).filter(
        func.lower(Player.name) == name.lower(),
        Player.server == server).first()
    if player:
        return player
    else:
        player = Player(name=name, server=server)
        s.add(player)
        s.commit()
        return player


def setup_servers(s):
    """Set up basic source data.

    Right now this just adds the 'unknown' source.
    """
    if not s.query(Server).filter(Server.name == '???').first():
        s.add(Server(name='???'))
        s.commit()


def setup_species(s):
    """Load species data into the database."""
    for sp in const.SPECIES:
        if not s.query(Species).filter(Species.short == sp.short).first():
            s.add(Species(short=sp.short, full=sp.full, playable=sp.playable))
    s.commit()


def setup_backgrounds(s):
    """Load background data into the database."""
    for bg in const.BACKGROUNDS:
        if not s.query(Background).filter(Background.short == bg.short).first(
        ):
            s.add(Background(short=bg.short,
                             full=bg.full,
                             playable=bg.playable))
    s.commit()


def setup_gods(s):
    """Load god data into the database."""
    for god in const.GODS:
        if not s.query(God).filter(God.name == god.name).first():
            s.add(God(name=god.name, playable=god.playable))
    s.commit()


def get_version(s, v):
    """Get a version, creating it if needed."""
    version = s.query(Version).filter(Version.v == v).first()
    if version:
        return version
    else:
        version = Version(v=v)
        s.add(version)
        s.commit()
        return version


def setup_branches(s):
    """Load branch data into the database."""
    for br in const.BRANCHES:
        if not s.query(Branch).filter(Branch.short == br.short).first():
            s.add(Branch(short=br.short, full=br.full, playable=br.playable))
    s.commit()


def get_place(s, branch, lvl):
    """Get a place, creating it if needed."""
    place = s.query(Place).filter(Place.branch == branch,
                                  Place.level == lvl).first()
    if place:
        return place
    else:
        place = Place(branch=branch, level=lvl)
        s.add(place)
        s.commit()
        return place


def get_species(s, sp):
    """Get a species, creating it if needed."""
    species = s.query(Species).filter(Species.short == sp).first()
    if species:
        return species
    else:
        species = Species(short=sp, full=sp, playable=False)
        s.add(species)
        s.commit()
        print("Warning: Found new species %s, please add me to constants.py"
              " and update the database." % sp)
        return species


def get_background(s, bg):
    """Get a background, creating it if needed."""
    background = s.query(Background).filter(Background.short == bg).first()
    if background:
        return background
    else:
        background = Background(short=bg, full=bg, playable=False)
        s.add(background)
        s.commit()
        print("Warning: Found new background %s, please add me to constants.py"
              " and update the database." % bg)
        return background


def get_god(s, name):
    """Get a god, creating it if needed."""
    god = s.query(God).filter(God.name == name).first()
    if god:
        return god
    else:
        god = God(name=name, playable=False)
        s.add(god)
        s.commit()
        print("Warning: Found new god %s, please add me to constants.py"
              " and update the database." % name)
        return god


def get_branch(s, br):
    """Get a branch, creating it if needed."""
    branch = s.query(Branch).filter(Branch.short == br).first()
    if branch:
        return branch
    else:
        branch = Branch(short=br, full=br, playable=False)
        s.add(branch)
        s.commit()
        print("Warning: Found new branch %s, please add me to constants.py"
              " and update the database." % name)
        return branch


@_reraise_dberror
def add_game(s, data):
    """Normalise and add a game to the database."""
    # Normalise some data
    data['god'] = const.GOD_NAME_FIXUPS.get(data['god'], data['god'])
    data['race'] = const.RACE_NAME_FIXUPS.get(data['race'], data['race'])

    game = Game()
    game.gid = data['gid']

    server = get_server(s, data['src'])
    game.player = get_player(s, data['name'], server)

    game.species = get_species(s, data['char'][:2])
    game.background = get_background(s, data['char'][2:])
    game.god = get_god(s, data['god'])
    game.v = get_version(s, data['v'])
    branch = get_branch(s, data['br'])
    game.place = get_place(s, branch, data['lvl'])
    game.xl = data['xl']
    game.tmsg = data['tmsg']
    game.turn = data['turn']
    game.dur = data['dur']
    game.runes = data.get('urune', 0)
    game.sc = data['sc']
    game.start = modelutils.crawl_date_to_datetime(data['start'])
    game.end = modelutils.crawl_date_to_datetime(data['end'])
    game.ktyp = data['ktyp']

    s.add(game)
    # XXX should move to s.bulk_insert_mappings(Game, (list of game dicts))


def setup_database(database):
    """Set up the database and create the master sessionmaker."""
    if database == 'mysql':
        DB_URI = 'mysql://localhost/dcss_scoreboard'
    elif database == 'sqlite':
        DB_URI = 'sqlite://'
    else:
        raise ValueError("Unknown database type!")
    ENGINE_OPTS = {}
    engine = sqlalchemy.create_engine(DB_URI, **ENGINE_OPTS)
    Base.metadata.create_all(engine)

    # Create the global session manager
    global Session
    Session = sessionmaker(bind=engine)

    sess = Session()

    setup_servers(sess)
    setup_species(sess)
    setup_backgrounds(sess)
    setup_gods(sess)
    setup_branches(sess)


def get_session():
    """Create a new database session."""
    return Session()


def get_logfile_progress(s, logfile):
    """Get a logfile progress records, creating it if needed."""
    log = s.query(LogfileProgress).filter(LogfileProgress.name ==
                                          logfile).first()
    if log:
        return log
    else:
        log = LogfileProgress(name=logfile)
        s.add(log)
        s.commit()
        return log


def save_logfile_progress(s, logfile, pos):
    """Save the position for a logfile."""
    log = get_logfile_progress(s, logfile)
    log.bytes_parsed = pos
    s.add(log)
    s.commit()
