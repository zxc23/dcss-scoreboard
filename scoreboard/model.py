"""Defines the database models for this module."""

from typing import Optional, Tuple, Callable, Sequence

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative  # for typing
from sqlalchemy import func

import scoreboard.constants as const
from scoreboard.orm import Server, Player, Species, Background, God, Version, \
    Branch, Place, Game, LogfileProgress, Achievement, Account, Ktyp, Streak
import scoreboard.modelutils as modelutils


class DBError(BaseException):
    """Generic wrapper for sqlalchemy errors passed out of this module."""

    pass


class DBIntegrityError(BaseException):
    """Generic wrapper for sqlalchemy sqlalchemy.exc.IntegrityError errors."""

    pass


def _reraise_dberror(function: Callable) -> Callable:
    """Re-raise errors from decorated function as DBError or DBIntegrityError.

    Doesn't re-wrap DBError/DBIntegrityError exceptions.
    """

    def f(*args, **kwargs):  # type: ignore
        """Wrap Sqlalchemy errors."""
        try:
            return function(*args, **kwargs)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            elif isinstance(e, DBError) or isinstance(e, DBIntegrityError):
                raise
            elif isinstance(e, sqlalchemy.exc.IntegrityError):
                raise DBIntegrityError from e
            else:
                raise DBError from e

    return f


def get_server(s: sqlalchemy.orm.session.Session, name: str) -> Server:
    """Get a server, creating it if needed."""
    server = s.query(Server).filter(Server.name == name).first()
    if server:
        return server
    else:
        server = Server(name=name)
        s.add(server)
        s.commit()
        return server


def get_account(s: sqlalchemy.orm.session.Session, name: str, server:
                Server) -> Account:
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


def get_player(s: sqlalchemy.orm.session.Session, name: str) -> Player:
    """Get a player's object, creating them if needed.

    Note that player names are not case sensitive, so names are stored with
    their canonical capitalisation but we always compare the lowercase version.
    """
    player = s.query(Player).filter(
        func.lower(Player.name) == name.lower()).first()
    if player:
        return player
    else:
        player = Player(name=name)
        s.add(player)
        s.commit()
        return player


def setup_species(s: sqlalchemy.orm.session.Session) -> None:
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


def setup_backgrounds(s: sqlalchemy.orm.session.Session) -> None:
    """Load background data into the database."""
    new = []
    for bg in const.BACKGROUNDS:
        if not s.query(Background).filter(
                Background.short == bg.short).first():
            print("Adding background '%s'" % bg.full)
            new.append({'short': bg.short,
                        'name': bg.full,
                        'playable': bg.playable})
    s.bulk_insert_mappings(Background, new)
    s.commit()


def setup_achievements(s: sqlalchemy.orm.session.Session) -> None:
    """Load manual achievements into the database."""
    for proto in const.ACHIEVEMENTS:
        if not s.query(Achievement).filter(
                Achievement.name == proto.name).one_or_none():
            print("Adding achievement '%s'" % proto.name)
            achievement = Achievement()
            achievement.key = proto.key
            achievement.name = proto.name
            achievement.description = proto.description
            s.add(achievement)
            for player_name in proto.players:
                print("Awarding achievement '%s' to '%s'" %
                      (achievement.name, player_name))
                player = get_player(s, player_name)
                player.achievements.append(achievement)
                s.add(player)
    s.commit()


def setup_gods(s: sqlalchemy.orm.session.Session) -> None:
    """Load god data into the database."""
    new = []
    for god in const.GODS:
        if not s.query(God).filter(God.name == god.name).first():
            print("Adding god '%s'" % god.name)
            new.append({'name': god.name, 'playable': god.playable})
    s.bulk_insert_mappings(God, new)
    s.commit()


def setup_ktyps(s: sqlalchemy.orm.session.Session) -> None:
    """Load ktyp data into the database."""
    new = []
    for ktyp in const.KTYPS:
        if not s.query(Ktyp).filter(Ktyp.name == ktyp).first():
            print("Adding ktyp '%s'" % ktyp)
            new.append({'name': ktyp})
    s.bulk_insert_mappings(Ktyp, new)
    s.commit()


def get_version(s: sqlalchemy.orm.session.Session, v: str) -> Version:
    """Get a version, creating it if needed."""
    version = s.query(Version).filter(Version.v == v).first()
    if version:
        return version
    else:
        version = Version(v=v)
        s.add(version)
        s.commit()
        return version


def setup_branches(s: sqlalchemy.orm.session.Session) -> None:
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


def get_place(s: sqlalchemy.orm.session.Session, branch: Branch, lvl:
              int) -> Place:
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


def get_species(s: sqlalchemy.orm.session.Session, sp: str) -> Species:
    """Get a species by short code, creating it if needed."""
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


def get_background(s: sqlalchemy.orm.session.Session, bg: str) -> Background:
    """Get a background by short code, creating it if needed."""
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


def get_god(s: sqlalchemy.orm.session.Session, name: str) -> God:
    """Get a god by name, creating it if needed."""
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


def get_ktyp(s: sqlalchemy.orm.session.Session, name: str) -> Ktyp:
    """Get a ktyp by name, creating it if needed."""
    ktyp = s.query(Ktyp).filter(Ktyp.name == name).first()
    if ktyp:
        return ktyp
    else:
        ktyp = Ktyp(name=name)
        s.add(ktyp)
        s.commit()
        print("Warning: Found new ktyp %s, please add me to constants.py" %
              name)
        return ktyp


def get_branch(s: sqlalchemy.orm.session.Session, br: str) -> Branch:
    """Get a branch by short name, creating it if needed."""
    branch = s.query(Branch).filter(Branch.short == br).first()
    if branch:
        return branch
    else:
        branch = Branch(short=br, name=br, multilevel=True, playable=False)
        s.add(branch)
        s.commit()
        print("Warning: Found new branch %s, please add me to constants.py"
              " and update the database." % br)
        return branch


def create_streak(s: sqlalchemy.orm.session.Session, player: Player) -> Streak:
    """Create a new streak for a given player."""
    streak = Streak(player_id=player.id, active=True)
    s.add(streak)
    s.commit()
    return streak


@_reraise_dberror
def add_game(s: sqlalchemy.orm.session.Session, game_data: dict) -> None:
    """Normalise and add a game to the database."""
    add_games(s, [game_data])


@_reraise_dberror
def add_games(s: sqlalchemy.orm.session.Session, games_data:
              Sequence[dict]) -> None:
    """Normalise and add multiple games to the database."""
    games = []
    for game in games_data:
        games.append(create_game_mapping(s, game))
    s.bulk_insert_mappings(Game, games)


def create_game_mapping(s: sqlalchemy.orm.session.Session, data: dict) -> dict:
    """Convert raw log dict into a game object."""

    # Normalise some data
    data['god'] = const.GOD_NAME_FIXUPS.get(data['god'], data['god'])
    data['race'] = const.SPECIES_NAME_FIXUPS.get(data['race'], data['race'])
    if data['char'][:2] in const.SPECIES_SHORTNAME_FIXUPS:
        oldrace = data['char'][:2]
        newrace = const.SPECIES_SHORTNAME_FIXUPS[oldrace]
        data['char'] = newrace + data['char'][2:]
    if data['char'][2:] in const.BACKGROUND_SHORTNAME_FIXUPS:
        oldbg = data['char'][2:]
        newbg = const.BACKGROUND_SHORTNAME_FIXUPS[oldbg]
        data['char'] = data['char'][:2] + newbg
    data['br'] = const.BRANCH_NAME_FIXUPS.get(data['br'], data['br'])
    data['ktyp'] = const.KTYP_FIXUPS.get(data['ktyp'], data['ktyp'])

    branch = get_branch(s, data['br'])
    server = get_server(s, data['src'])
    game = {
        'gid': data['gid'],
        'account_id': get_account(s, data['name'], server).id,
        'species_id': get_species(s, data['char'][:2]).id,
        'background_id': get_background(s, data['char'][2:]).id,
        'god_id': get_god(s, data['god']).id,
        'version_id': get_version(s, data['v']).id,
        'place_id': get_place(s, branch, data['lvl']).id,
        'xl': data['xl'],
        'tmsg': data['tmsg'],
        'turn': data['turn'],
        'dur': data['dur'],
        'runes': data.get('urune', 0),
        'score': data['sc'],
        'start': modelutils.crawl_date_to_datetime(data['start']),
        'end': modelutils.crawl_date_to_datetime(data['end']),
        'ktyp_id': get_ktyp(s, data['ktyp']).id,
        'potions_used': data.get('potionsused', -1),
        'scrolls_used': data.get('scrollsused', -1),
        'dam': data['dam'],
        'tdam': data.get('tdam', data['dam']),
        'sdam': data.get('sdam', data['dam']),
    }

    return game


def get_logfile_progress(s: sqlalchemy.orm.session.Session, logfile:
                         str) -> LogfileProgress:
    """Get a logfile progress records, creating it if needed."""
    log = s.query(LogfileProgress).filter(
        LogfileProgress.name == logfile).first()
    if log:
        return log
    else:
        log = LogfileProgress(name=logfile)
        s.add(log)
        s.commit()
        return log


def save_logfile_progress(s: sqlalchemy.orm.session.Session, logfile: str, pos:
                          int) -> None:
    """Save the position for a logfile."""
    log = get_logfile_progress(s, logfile)
    log.bytes_parsed = pos
    s.add(log)
    s.commit()


def list_accounts(s: sqlalchemy.orm.session.Session,
                  *,
                  blacklisted: Optional[bool]=None) -> Sequence[Account]:
    """Get a list of all accounts.

    If blacklisted is specified, only return accounts with that blacklisted
    value.
    """
    q = s.query(Account)
    if blacklisted is not None:
        q = q.filter(Account.blacklisted ==
                     (sqlalchemy.true()
                      if blacklisted else sqlalchemy.false()))
    results = q.all()
    return results


def list_players(s: sqlalchemy.orm.session.Session) -> Sequence[Player]:
    """Get a list of all players."""
    q = s.query(Player)
    return q.all()


def _generic_char_type_lister(s: sqlalchemy.orm.session.Session, *,
                              cls: sqlalchemy.ext.declarative.api.DeclarativeMeta,
                              playable: Optional[bool]) \
        -> Sequence:
    q = s.query(cls)
    if playable is not None:
        # Type[Any] has no attribute "playable"
        q = q.filter(cls.playable == (sqlalchemy.true()
                                      if playable else sqlalchemy.false()))
    return q.order_by(getattr(cls, 'name')).all()


def list_species(s: sqlalchemy.orm.session.Session,
                 *,
                 playable: Optional[bool]=None) -> Sequence[Species]:
    """Return a list of species.

    Parameters:
        Playable: if specified, only return species with matching playable
            status.
    """
    return _generic_char_type_lister(s, cls=Species, playable=playable)


def list_backgrounds(s: sqlalchemy.orm.session.Session,
                     *,
                     playable: Optional[bool]=None) -> Sequence[Background]:
    """Return a list of backgrounds.

    Parameters:
        Playable: if specified, only return species with matching playable
            status.
    """
    return _generic_char_type_lister(s, cls=Background, playable=playable)


def list_gods(s: sqlalchemy.orm.session.Session,
              *,
              playable: Optional[bool]=None) -> Sequence[God]:
    """Return a list of gods.

    Parameters:
        Playable: if specified, only return species with matching playable
            status.
    """
    return _generic_char_type_lister(s, cls=God, playable=playable)


def _games(s: sqlalchemy.orm.session.Session,
           *,
           player: Optional[Player]=None,
           account: Optional[Account]=None,
           scored: Optional[bool]=None,
           limit: Optional[int]=None,
           gid: Optional[str]=None,
           winning: Optional[bool]=None,
           reverse_order: Optional[bool]=False) -> sqlalchemy.orm.query.Query:
    """Build a query to match games with certain conditions.

    Parameters:
        player: If specified, only return games with a matching player
        account: If specified, only return games with a matching account
        scored: If specified, only return games with a matching scored
        limit: If specified, return up to limit games
        gid: If specified, only return game with matching gid
        winning: If specified, only return games where ktyp==/!='winning'
        reverse_order: If specified, return games least->most recent (if True),
            or most->least recent (if False)

    Returns:
        query object you can call.
    """
    q = s.query(Game)
    if player is not None:
        q = q.join(Game.account).join(Account.player).filter(
            Player.id == player.id)
    if account is not None:
        q = q.join(Game.account).filter(Account.id == account.id)
    if scored is not None:
        q = q.filter(Game.scored == (sqlalchemy.true()
                                     if scored else sqlalchemy.false()))
    if gid is not None:
        q = q.filter(Game.gid == gid)
    if winning is not None:
        ktyp = get_ktyp(s, 'winning')
        if winning:
            q = q.filter(Game.ktyp_id == ktyp.id)
        else:
            q = q.filter(Game.ktyp_id != ktyp.id)
    if reverse_order is not None:
        q = q.order_by(Game.end.desc()
                       if not reverse_order else Game.end.asc())
    if limit is not None:
        q = q.limit(limit)
    return q


def list_games(s: sqlalchemy.orm.session.Session,
               *,
               player: Optional[Player]=None,
               account: Optional[Account]=None,
               scored: Optional[bool]=None,
               limit: Optional[int]=None,
               gid: Optional[str]=None,
               winning: Optional[bool]=None,
               reverse_order: bool=False) -> Sequence[Game]:
    """Get a list of all games that match specified conditions.

    See _games documentation for parameters.

    Return:
        list of Games.
    """
    return _games(
        s,
        player=player,
        account=account,
        scored=scored,
        limit=limit,
        gid=gid,
        winning=winning,
        reverse_order=reverse_order).all()


def count_games(s: sqlalchemy.orm.session.Session,
                *,
                player: Optional[Player]=None,
                account: Optional[Account]=None,
                scored: Optional[bool]=None,
                gid: Optional[str]=None,
                winning: Optional[bool]=None) -> int:
    """Get a count of all games that match specified conditions.

    See _games documentation for parameters.

    Return:
        count of matching Games.
    """
    return _games(
        s,
        player=player,
        account=account,
        scored=scored,
        gid=gid,
        winning=winning).count()


def get_game(s: sqlalchemy.orm.session.Session, **kwargs: dict) -> Game:
    """Get a single game. See get_games docstring/type signature."""
    kwargs.setdefault('limit', 1)  # type: ignore
    result = list_games(s, **kwargs)  # type: ignore
    if not result:
        return None
    else:
        return result[0]


def get_achievement(s: sqlalchemy.orm.session.Session, key:
                    str) -> Achievement:
    """Get an achievement."""
    return s.query(Achievement).filter(Achievement.key == key).one()


def highscores(s: sqlalchemy.orm.session.Session,
               *,
               limit: int=const.GLOBAL_TABLE_LENGTH) -> Sequence[Game]:
    """Return up to limit high scores.

    Fewer games may be returned if there is not enough matching data.
    """
    q = s.query(Game).order_by(Game.score.desc()).limit(limit)
    return q.all()


# TODO: type game_column
def _highscores_helper(
        s: sqlalchemy.orm.session.Session, mapped_class:
        sqlalchemy.ext.declarative.api.DeclarativeMeta, game_column:
        sqlalchemy.orm.attributes.InstrumentedAttribute) -> Sequence[Game]:
    """Generic function to find highscores against arbitrary foreign keys.

    Parameters:
        mapped_class: the foreign key table's class
        game_column: the foreign key's column in Games table

    Returns:
        Array of results
    """
    results = []
    q = s.query(Game)
    for i in s.query(mapped_class).filter(
            # error: Type[Any] has no attribute "playable"
            mapped_class.playable ==
            sqlalchemy.true()).order_by(mapped_class.name).all():
        result = q.filter(
            game_column == i).order_by(Game.score.desc()).limit(1).first()
        if result:
            results.append(result)
    return results


def species_highscores(s: sqlalchemy.orm.session.Session) -> Sequence[Game]:
    """Return the top score for each playable species.

    Not every species may have a game in the database.
    """
    return _highscores_helper(s, Species, Game.species)


def background_highscores(s: sqlalchemy.orm.session.Session) -> Sequence[Game]:
    """Return the top score for each playable background.

    Not every background may have a game in the database.
    """
    return _highscores_helper(s, Background, Game.background)


def god_highscores(s: sqlalchemy.orm.session.Session) -> Sequence[Game]:
    """Return the top score for each playable god.

    Not every god may have a game in the database.
    """
    return _highscores_helper(s, God, Game.god)


def combo_highscores(s: sqlalchemy.orm.session.Session) -> Sequence[Game]:
    """Return the top score for each playable combo.

    Not every combo may have a game in the database.
    """
    results = []
    q = s.query(Game).order_by(Game.score.desc())
    for sp in s.query(Species).filter(
            Species.playable == sqlalchemy.true()).order_by('name').all():
        for bg in s.query(Background).filter(
                Background.playable ==
                sqlalchemy.true()).order_by('name').all():
            query = q.filter(Game.species == sp, Game.background == bg)
            result = query.first()
            if result:
                results.append(result)

    return results


def fastest_wins(s: sqlalchemy.orm.session.Session,
                 *,
                 limit: int=const.GLOBAL_TABLE_LENGTH,
                 exclude_bots: bool=True) -> Sequence[Game]:
    """Return up to limit fastest wins.

    exclude_bots: If True, exclude known bot accounts from the rankings.
    """
    ktyp = get_ktyp(s, 'winning')
    q = s.query(Game).filter(Game.ktyp == ktyp).order_by('dur')
    if exclude_bots:
        q = q.join(Game.account).join(Account.player)
        for bot_name in const.BLACKLISTS['bots']:
            bot = get_player(s, bot_name)
            q = q.filter(Player.id != bot.id)
    return q.limit(limit).all()


def shortest_wins(s: sqlalchemy.orm.session.Session,
                  *,
                  limit: int=const.GLOBAL_TABLE_LENGTH) -> Sequence[Game]:
    """Return up to limit shortest wins."""
    ktyp = get_ktyp(s, 'winning')
    return s.query(Game).filter(
        Game.ktyp == ktyp).order_by('turn').limit(limit).all()


def combo_highscore_holders(s: sqlalchemy.orm.session.Session,
                            limit: int=const.GLOBAL_TABLE_LENGTH) \
        -> Sequence[Tuple[Player, Sequence[Game]]]:
    """Return the players with the most combo highscores.

    May return fewer than limit names.

    Returns a list of (player, games) tuples.
    """
    highscore_games = combo_highscores(s)
    results = {}  # type: dict
    for game in highscore_games:
        player = game.account.player.name
        results.setdefault(player, []).append(game)

    return sorted(
        results.items(), key=lambda i: len(i[1]), reverse=True)[:limit]


def get_gobal_records(s: sqlalchemy.orm.session.Session) -> dict:
    """Convenience function to return all classes of highscores."""
    out = {
        'combo': combo_highscores(s),
        'species': species_highscores(s),
        'background': background_highscores(s),
        'god': god_highscores(s),
        'shortest': shortest_wins(s),
        'fastest': fastest_wins(s),
    }
    return out


def get_player_streak(s: sqlalchemy.orm.session.Session, player:
                      Player) -> Optional[Streak]:
    """Get a player's active streak.

    Returns None if they don't have a currently active streak.
    Note: a streak may be one game long.
    """
    q = s.query(Streak).filter(Streak.player == player,
                               Streak.active == sqlalchemy.true())
    return q.one_or_none()


def get_streaks(s: sqlalchemy.orm.session.Session,
                active: Optional[bool]=None,
                limit: Optional[int]=None,
                max_age: Optional[int]=None,
                ) \
        -> Sequence[Streak]:
    """Get streaks, ordered by length (longest first).

    Parameters:
        active: only return streaks with this active flag
        limit: only return (up to) limit results
        max_age: only return streaks with a win less than this many days old

    Returns:
        List of active streaks.
    """
    # The following code is a translation of this basic SQL:
    # SELECT streaks.*, count(games.streak_id) as streak_length
    # FROM streaks
    # JOIN games ON (streaks.id = games.streak_id)
    # GROUP BY streaks.id
    # HAVING streak_length > 1
    # ORDER BY streak_length DESC
    streak_length = func.count(Game.streak_id).label('streak_length')
    streak_last_activity = func.max(Game.end).label('streak_last_activity')
    q = s.query(Streak, streak_length).join(Streak.games)
    q = q.group_by(Streak.id)
    q = q.having(streak_length > 1)
    if max_age is not None:
        q = q.having(
            streak_last_activity > func.date('now', '-%s day' % max_age))
    q = q.order_by(streak_length.desc())
    if active is not None:
        q = q.filter(Streak.active == (sqlalchemy.true()
                                       if active else sqlalchemy.false()))
    if limit is not None:
        q = q.limit(limit)
    streaks = q.all()
    # Since we added a column to the query, the result format is:
    # ((Streak, length), (Streak, length), ...)
    # It's annoying to deal with a custom format, and recalculating the streak
    # length for a few streaks is NBD, so just return a list of Streaks
    return [t.Streak for t in streaks]


def list_achievements(s:
                      sqlalchemy.orm.session.Session) -> Sequence[Achievement]:
    """Get all streaks."""
    return s.query(Achievement).all()
