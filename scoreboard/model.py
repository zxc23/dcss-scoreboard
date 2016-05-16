"""Defines the database models for this module."""

import os
import json

from sqlalchemy import func

from . import constants as const
from .orm import Server, Player, Species, Background, God, Version, \
    Branch, Place, Game, LogfileProgress, Achievement, Account
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


def get_account(s, name, server):
    """Get a player's object, creating them if needed.

    Note that player names are not case sensitive, so names are stored with
    their canonical capitalisation but we always compare the lowercase version.
    """
    player = get_player(s, name)
    acc = s.query(Account).filter(
        func.lower(Account.name) == name.lower(),
        Account.server == server).first()
    if acc:
        return acc
    else:
        acc = Account(name=name, server=server, player=player)
        s.add(acc)
        s.commit()
        return acc


def get_player(s, name):
    """Get a player's object, creating them if needed.

    Note that player names are not case sensitive, so names are stored with
    their canonical capitalisation but we always compare the lowercase version.
    """
    player = s.query(Player).filter(Player.name == name.lower()).first()
    if player:
        return player
    else:
        player = Player(name=name)
        s.add(player)
        s.commit()
        return player


def setup_servers(s):
    """Set up basic source data.

    Right now this just adds the 'unknown' source.
    """
    if not s.query(Server).filter(Server.name == '???').first():
        print("Adding server '???'")
        s.add(Server(name='???'))
        s.commit()


def setup_species(s):
    """Load species data into the database."""
    new = []
    for sp in const.SPECIES:
        if not s.query(Species).filter(Species.short == sp.short).first():
            print("Adding species '%s'" % sp.full)
            new.append({'short': sp.short,
                        'full': sp.full,
                        'playable': sp.playable})
    s.bulk_insert_mappings(Species, new)
    s.commit()


def setup_backgrounds(s):
    """Load background data into the database."""
    new = []
    for bg in const.BACKGROUNDS:
        if not s.query(Background).filter(Background.short == bg.short).first(
        ):
            print("Adding background '%s'" % bg.full)
            new.append({'short': bg.short,
                        'full': bg.full,
                        'playable': bg.playable})
    s.bulk_insert_mappings(Background, new)
    s.commit()


def setup_achievements(s):
    """Load manual achievements into the database."""
    new = []
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    with open(path) as f:
        achievements = json.load(f)
    for a in achievements:
        if not s.query(Achievement).filter(Achievement.name == a[
                'name']).first():
            print("Adding achievement '%s'" % a['name'])
            new.append({'name': a['name'], 'key': a['id'], 'description': a['description']})
    s.bulk_insert_mappings(Achievement, new)
    s.commit()


def setup_gods(s):
    """Load god data into the database."""
    new = []
    for god in const.GODS:
        if not s.query(God).filter(God.name == god.name).first():
            print("Adding god '%s'" % god.name)
            new.append({'name': god.name, 'playable': god.playable})
    s.bulk_insert_mappings(God, new)
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
    new = []
    for br in const.BRANCHES:
        if not s.query(Branch).filter(Branch.short == br.short).first():
            print("Adding branch '%s'" % br.full)
            new.append({'short': br.short,
                        'full': br.full,
                        'playable': br.playable})
    s.bulk_insert_mappings(Branch, new)
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
              " and update the database." % br)
        return branch


@_reraise_dberror
def add_game(s, game_data):
    """Normalise and add a game to the database."""
    add_games(s, [game_data])


@_reraise_dberror
def add_games(s, games_data):
    """Normalise and add multiple games to the database."""
    games = []
    for game in games_data:
        games.append(create_game_mapping(s, game))
    s.bulk_insert_mappings(Game, games)


def create_game_mapping(s, data):
    """Convert raw log dict into a game object."""
    # Normalise some data
    data['god'] = const.GOD_NAME_FIXUPS.get(data['god'], data['god'])
    data['race'] = const.RACE_NAME_FIXUPS.get(data['race'], data['race'])

    game = {}
    game['gid'] = data['gid']
    server = get_server(s, data['src'])
    game['account_id'] = get_account(s, data['name'], server).id
    game['species_id'] = get_species(s, data['char'][:2]).id
    game['background_id'] = get_background(s, data['char'][2:]).id
    game['god_id'] = get_god(s, data['god']).id
    game['version_id'] = get_version(s, data['v']).id
    branch = get_branch(s, data['br'])
    game['place_id'] = get_place(s, branch, data['lvl']).id
    game['xl'] = data['xl']
    game['tmsg'] = data['tmsg']
    game['turn'] = data['turn']
    game['dur'] = data['dur']
    game['runes'] = data.get('urune', 0)
    game['sc'] = data['sc']
    game['start'] = modelutils.crawl_date_to_datetime(data['start'])
    game['end'] = modelutils.crawl_date_to_datetime(data['end'])
    game['ktyp'] = data['ktyp']

    return game


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


def list_accounts(s, *, blacklisted=None):
    """Get a list of all players.

    If blacklisted is specified, only return players with that blacklisted
    value.
    """
    q = s.query(Account)
    if blacklisted is not None:
        q = q.filter(Account.blacklisted == blacklisted)
    results = q.all()
    return results


def list_games(s, *, scored=None, limit=None):
    """Get a lit of all games.

    If scored is specified, only return games with that scored value.
    If limit is specified, return up to limit games.
    """
    q = s.query(Game)
    if scored is not None:
        q = q.filter(Game.scored == scored)
    if limit is not None:
        q = q.limit(limit)
    results = q.all()
    return results


def get_achievement(s, key):
    """Get an achievement."""
    return s.query(Achievement).filter(Achievement.key == key).first()
