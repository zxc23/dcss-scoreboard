"""Defines the database models for this module."""

import os
import json

from typing import Union

from sqlalchemy import func

import scoreboard.constants as const
from scoreboard.orm import Server, Player, Species, Background, God, Version, \
    Branch, Place, Game, LogfileProgress, Achievement, Account
import scoreboard.modelutils as modelutils


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
                        'name': sp.full,
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
                        'name': bg.full,
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
                        'name': br.full,
                        'multilevel': br.multilevel,
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
        species = Species(short=sp, name=sp, playable=False)
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
        background = Background(short=bg, name=bg, playable=False)
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
        branch = Branch(short=br, name=br, playable=False)
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
    game['score'] = data['sc']
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
    """Get a list of all accounts.

    If blacklisted is specified, only return accounts with that blacklisted
    value.
    """
    q = s.query(Account)
    if blacklisted is not None:
        q = q.filter(Account.blacklisted == blacklisted)
    results = q.all()
    return results


def list_players(s):
    """Get a list of all players."""
    q = s.query(Player)
    return q.all()


def list_games(s, *,
               player: Union[bool, None]=None,
               scored: Union[bool, None]=None,
               limit: Union[int, None]=None,
               gid: Union[str, None]=None,
               winning: Union[bool, None]=None) -> list:
    """Get a list of all games that match a specified condition.

    If scored is specified, only return games with that scored value.
    If limit is specified, return up to limit games.
    """
    q = s.query(Game)
    if player is not None:
        q = q.join(Game.account).join(Account.player).filter(Player.name == player)
    if scored is not None:
        q = q.filter(Game.scored == scored)
    if gid is not None:
        q = q.filter(Game.gid == gid)
    if winning is not None:
        if winning:
            q = q.filter(Game.ktyp == 'winning')
        else:
            q = q.filter(Game.ktyp != 'winning')
    q = q.order_by(Game.end.desc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def get_game(s, **kwargs) -> Game:
    """Get a single game."""
    kwargs.setdefault('limit', 1)
    result = list_games(s, **kwargs)
    if not result:
        return None
    else:
        return result[0]


def get_achievement(s, key):
    """Get an achievement."""
    return s.query(Achievement).filter(Achievement.key == key).first()


def highscores(s, *, limit=const.GLOBAL_TABLE_LENGTH):
    """Return up to limit high scores.

    Fewer games may be returned if there is not enough matching data.
    """
    q = s.query(Game).order_by(Game.score.desc()).limit(limit)
    return q.all()


def _highscores_helper(s, mapped_class, game_column):
    """Generic function to find highscores against arbitrary foreign keys.

    Parameters:
        mapped_class: the foreign key table's class
        game_column: the foreign key's column in Games table

    Returns:
        Array of results
    """
    results = []
    q = s.query(Game)
    for i in s.query(mapped_class).filter(mapped_class.playable == True).order_by(mapped_class.name).all():
        result = q.filter(game_column == i).order_by(
            Game.score).limit(1).first()
        if result:
            results.append(result)
    return results


def species_highscores(s):
    """Return the top score for each playable species.

    Not every species may have a game in the database.
    """
    return _highscores_helper(s, Species, Game.species)

def background_highscores(s):
    """Return the top score for each playable background.

    Not every background may have a game in the database.
    """
    return _highscores_helper(s, Background, Game.background)

def god_highscores(s):
    """Return the top score for each playable god.

    Not every god may have a game in the database.
    """
    return _highscores_helper(s, God, Game.god)


def combo_highscores(s):
    """Return the top score for each playable combo.

    Not every combo may have a game in the database.
    """
    results = []
    q = s.query(Game)
    for sp in s.query(Species).filter(Species.playable == True).all():
        for bg in s.query(Background).filter(Background.playable == True).all():
            result = q.filter(Game.species == sp, Game.background == bg).order_by(Game.score).limit(1).first()
            if result:
                results.append(result)

    return results


def fastest_wins(s, *, limit=const.GLOBAL_TABLE_LENGTH):
    """Return up to limit fastest wins."""
    return s.query(Game).filter(Game.ktyp == 'winning').order_by('dur').limit(limit).all()


def shortest_wins(s, *, limit=const.GLOBAL_TABLE_LENGTH):
    """Return up to limit shortest wins."""
    return s.query(Game).filter(Game.ktyp == 'winning').order_by('turn').limit(limit).all()


def combo_highscore_holders(s, limit=const.GLOBAL_TABLE_LENGTH):
    """Return the players with the most combo highscores.

    May return fewer than limit names.

    Returns a list of (player, games) tuples.
    """
    results = combo_highscores(s)
    all = {}
    for game in results:
        player = game.account.player.name
        if player not in all:
            all[player] = [game]
        else:
            all[player].append(game)

    return sorted(all.items(), key=lambda i: len(i[1]), reverse=True)[:limit]


def get_gobal_records(s):
    out = {}
    out['combo'] = combo_highscores(s)
    out['species'] = species_highscores(s)
    out['background'] = background_highscores(s)
    out['god'] = god_highscores(s)
    out['shortest'] = shortest_wins(s)
    out['fastest'] = fastest_wins(s)
    return out