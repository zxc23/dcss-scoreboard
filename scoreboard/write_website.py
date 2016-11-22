"""Take generated score data and write out all website files."""

import os
import json
import time
import datetime
import subprocess
import collections
import random
import shutil
import sys

from typing import Iterable, Optional, Sequence

import jsmin
import jinja2
import sqlalchemy.orm  # for sqlalchemy.orm.session.Session type hints

from . import model
from . import webutils
from . import orm
from . import constants as const

WEBSITE_DIR = 'website'


def rsync_replacement(src: str, dst: str) -> None:
    """Poor replacement for rsync on win32.

    Needed because shutil.copytree can't handle already existing dest dir.
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            rsync_replacement(s, d)
        else:
            shutil.copy2(s, d)


def _write_file(*, path: str, data: str) -> None:
    """Write a file."""
    with open(path, 'w', encoding='utf8') as f:
        f.write(data)


def jinja_env(
        urlbase: Optional[str],
        s: sqlalchemy.orm.session.Session) -> jinja2.environment.Environment:
    """Create the Jinja template environment."""
    template_path = os.path.join(os.path.dirname(__file__), 'html_templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters['prettyint'] = webutils.prettyint
    env.filters['prettyhours'] = webutils.prettyhours
    env.filters['prettydur'] = webutils.prettydur
    env.filters['prettycounter'] = webutils.prettycounter
    env.filters['prettycrawldate'] = webutils.prettycrawldate
    env.filters['streakstotable'] = webutils.streakstotable
    env.filters['prettydate'] = webutils.prettydate
    env.filters['link_player'] = webutils.link_player
    env.filters['morgue_link'] = webutils.morgue_link
    env.filters['percentage'] = webutils.percentage
    env.filters['mosthighscorestotable'] = webutils.mosthighscorestotable
    env.filters['recordsformatted'] = webutils.recordsformatted
    env.filters['shortest_win'] = webutils.shortest_win
    env.filters['fastest_win'] = webutils.fastest_win
    env.filters['highscore'] = webutils.highscore

    env.filters['generic_games_to_table'] = webutils.generic_games_to_table
    env.filters[
        'generic_highscores_to_table'] = webutils.generic_highscores_to_table
    env.filters[
        'species_highscores_to_table'] = webutils.species_highscores_to_table
    env.filters[
        'background_highscores_to_table'] = webutils.background_highscores_to_table

    env.globals['tableclasses'] = const.TABLE_CLASSES
    env.globals['playable_species'] = model.list_species(s, playable=True)
    env.globals['playable_backgrounds'] = model.list_backgrounds(
        s, playable=True)
    env.globals['playable_gods'] = model.list_gods(s, playable=True)
    env.globals['current_time'] = datetime.datetime.utcnow()

    if urlbase:
        env.globals['urlbase'] = urlbase
    else:
        env.globals['urlbase'] = os.path.join(os.getcwd(), WEBSITE_DIR)

    return env


def _mkdir(path: str) -> None:
    if not os.path.isdir(path):
        print("mkdir %s/" % path)
        os.mkdir(path)


def setup_website_dir(env: jinja2.environment.Environment,
                      path: str,
                      all_players: Iterable) -> None:
    """Create the website dir and add static content."""
    print("Writing HTML to %s" % path)

    _mkdir(path)
    _mkdir(os.path.join(path, 'api'))
    _mkdir(os.path.join(path, 'api', '1'))
    _mkdir(os.path.join(path, 'api', '1', 'player'))
    _mkdir(os.path.join(path, 'api', '1', 'player', 'wins'))

    print("Copying static assets")
    src = os.path.join(os.path.dirname(__file__), 'html_static')
    dst = os.path.join(path, 'static')
    if sys.platform != 'win32':
        subprocess.run(['rsync', '-a', src + '/', dst + '/'])
    else:
        rsync_replacement(src, dst)

    print("Generating player list")
    _write_file(
        path=os.path.join(dst, 'js', 'players.json'),
        data=json.dumps([p.name for p in all_players]))

    print("Writing minified local JS")
    js_template = env.get_template('dcss-scoreboard.js')
    _write_file(
        path=os.path.join(WEBSITE_DIR, 'static/js/dcss-scoreboard.js'),
        data=jsmin.jsmin(js_template.render()))


def render_index(s: sqlalchemy.orm.session.Session,
                 template: jinja2.environment.Template) -> str:
    """Render the index page."""
    return template.render(
        recent_wins=model.list_games(
            s, winning=True, limit=const.FRONTPAGE_TABLE_LENGTH),
        active_streaks=[],
        overall_highscores=model.highscores(
            s, limit=const.FRONTPAGE_TABLE_LENGTH),
        combo_high_scores=model.combo_highscore_holders(
            s, limit=const.FRONTPAGE_TABLE_LENGTH))


def write_index(s: sqlalchemy.orm.session.Session,
                env: jinja2.environment.Environment) -> None:
    """Write the index page."""
    print("Writing index")
    template = env.get_template('index.html')
    data = render_index(s, template)
    _write_file(path=os.path.join(WEBSITE_DIR, 'index.html'), data=data)


def write_404(env: jinja2.environment.Environment) -> None:
    """Write the 404 page."""
    print("Writing 404")
    template = env.get_template('404.html')
    _write_file(
        path=os.path.join(WEBSITE_DIR, '404.html'), data=template.render())


def write_streaks(s: sqlalchemy.orm.session.Session,
                  env: jinja2.environment.Environment) -> None:
    """Write the streak page."""
    print("Writing streaks")
    template = env.get_template('streaks.html')
    active_streaks = model.get_streaks(s, active=True, max_age=365)
    best_streaks = model.get_streaks(s, limit=10)
    _write_file(
        path=os.path.join(WEBSITE_DIR, 'streaks.html'),
        data=template.render(
            active_streaks=active_streaks, best_streaks=best_streaks))


def render_highscores(s: sqlalchemy.orm.session.Session,
                      template: jinja2.environment.Template) -> str:
    """Render the highscores page."""
    overall_highscores = model.highscores(s)
    species_highscores = model.species_highscores(s)
    background_highscores = model.background_highscores(s)
    god_highscores = model.god_highscores(s)
    combo_highscores = model.combo_highscores(s)
    fastest_wins = model.fastest_wins(s, exclude_bots=True)
    shortest_wins = model.shortest_wins(s)
    return template.render(
        overall_highscores=overall_highscores,
        species_highscores=species_highscores,
        background_highscores=background_highscores,
        god_highscores=god_highscores,
        combo_highscores=combo_highscores,
        fastest_wins=fastest_wins,
        shortest_wins=shortest_wins)


def write_highscores(s: sqlalchemy.orm.session.Session,
                     env: jinja2.environment.Environment) -> None:
    """Write the highscores page."""
    print("Writing highscores")
    template = env.get_template('highscores.html')
    data = render_highscores(s, template)
    _write_file(path=os.path.join(WEBSITE_DIR, 'highscores.html'), data=data)


def _get_player_records(global_records: dict, player: orm.Player) -> dict:
    out = {}  # type: dict
    for typ, games in global_records.items():
        for game in games:
            if game.player.name == player:
                if typ not in out:
                    out[typ] = [game]
                else:
                    out[typ].append(game)
    return out


def _wins_per_species(s: sqlalchemy.orm.session.Session,
                      games: Iterable[orm.Game],
                      playable: bool=True) -> Iterable[orm.Game]:
    """Return a dict of form {<Species 'Ce'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for sp in model.list_species(s, playable=playable):
        matching_games = [g for g in games if g.won and g.species == sp]
        # For playable=True, add every species to the output.
        # For playable=False, only add ones with wins
        if playable or matching_games:
            out[sp] = matching_games
    return out


def _wins_per_background(s: sqlalchemy.orm.session.Session,
                         games: Iterable[orm.Game],
                         playable: bool=True) -> Iterable[orm.Game]:
    """Return a dict of form {<Background 'Be'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for bg in model.list_backgrounds(s, playable=playable):
        matching_games = [g for g in games if g.won and g.background == bg]
        # For playable=True, add every background to the output.
        # For playable=False, only add ones with wins
        if playable or matching_games:
            out[bg] = matching_games
    return out


def _wins_per_god(s: sqlalchemy.orm.session.Session,
                  games: Iterable[orm.Game],
                  playable: bool=True) -> Iterable[orm.Game]:
    """Return a dict of form {<God 'Beogh'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for god in model.list_gods(s, playable=playable):
        matching_games = [g for g in games if g.won and g.god == god]
        # For playable=True, add every god to the output.
        # For playable=False, only add ones with wins
        if playable or matching_games:
            out[god] = matching_games
    return out


def render_player_page(s: sqlalchemy.orm.session.Session,
                       template: jinja2.environment.Template,
                       player: orm.Player,
                       global_records: dict) -> str:
    """Render an individual player's page."""
    n_games = model.count_games(s, player=player)
    # Don't make pages for players with no games played
    if n_games == 0:
        return ''

    # XXX: potential memory hog
    won_games = model.list_games(s, player=player, winning=True)
    n_won_games = len(won_games)
    species_wins = _wins_per_species(s, won_games)
    unplayable_species_wins = _wins_per_species(s, won_games, playable=False)
    background_wins = _wins_per_background(s, won_games)
    unplayable_background_wins = _wins_per_background(
        s, won_games, playable=False)
    god_wins = _wins_per_god(s, won_games)
    unplayable_god_wins = _wins_per_god(s, won_games, playable=False)
    shortest_win = min(won_games, default=None, key=lambda g: g.turn)
    fastest_win = min(won_games, default=None, key=lambda g: g.dur)

    records = _get_player_records(global_records, player)
    active_streak = model.get_player_streak(s, player)
    n_boring_games = model.count_games(s, player=player, boring=True)
    total_dur = model.total_duration(s, player=player)
    highscore = model.highscores(s, player=player, limit=1)[0]
    recent_games = model.list_games(
        s, player=player, limit=const.PLAYER_TABLE_LENGTH)

    return template.render(
        player=player,
        records=records,
        species_wins=species_wins,
        background_wins=background_wins,
        god_wins=god_wins,
        unplayable_species_wins=unplayable_species_wins,
        unplayable_background_wins=unplayable_background_wins,
        unplayable_god_wins=unplayable_god_wins,
        active_streak=active_streak,
        n_games=n_games,
        n_won_games=n_won_games,
        n_boring_games=n_boring_games,
        total_dur=total_dur,
        highscore=highscore,
        shortest_win=shortest_win,
        fastest_win=fastest_win,
        recent_games=recent_games,
        won_games=won_games)


def write_player_page(player_html_path: str, name: str, data: str) -> None:
    """Write an individual player's page."""
    _write_file(path=os.path.join(player_html_path, name + '.html'), data=data)


def write_player_pages(s: sqlalchemy.orm.session.Session,
                       env: jinja2.environment.Environment,
                       players: Sequence) -> None:
    """Write all player pages."""
    print("Writing %s player pages... " % len(players))
    start2 = time.time()
    player_html_path = os.path.join(WEBSITE_DIR, 'players')
    if not os.path.exists(player_html_path):
        os.mkdir(player_html_path)
    global_records = model.get_gobal_records(s)
    template = env.get_template('player.html')

    n = 0
    for player in players:
        data = render_player_page(s, template, player, global_records)
        write_player_page(player_html_path, player.url_name, data)
        model.updated_player_page(s, player)
        n += 1
        if not n % 100:
            print(n)
    s.commit()
    end = time.time()
    print("Wrote player pages in %s seconds" % round(end - start2, 2))


def write_player_api(s: sqlalchemy.orm.session.Session,
                     env: jinja2.environment.Environment,
                     players: Sequence) -> None:
    """Write all player API pages."""
    print("Writing player API pages")
    for player in players:
        won_games = model.list_games(s, player=player, winning=True)
        data = json.dumps(
            [g.as_dict() for g in won_games], sort_keys=True, indent=2)
        path = os.path.join(WEBSITE_DIR, 'api', '1', 'player', 'wins',
                            player.url_name)
        _write_file(path=path, data=data)


def write_website(players: Optional[Iterable],
                  urlbase: str,
                  extra_player_pages: int) -> None:
    """Write all website files.

    Paramers:
        urlbase (str) Base URL for the website
        players (iterable of strings) Only write these player pages.
            Pass in the player's name, not the entire Player object.
            If you pass in None, all player pages will be rebuilt.
            If you pass in any other false value, no player pages will be
              rebuilt.
    """
    start = time.time()

    s = orm.get_session()

    env = jinja_env(urlbase, s)

    # We need the list of all players to generate players.json
    all_players = sorted(model.list_players(s), key=lambda p: p.name)

    # Figure out what player pages to generate
    if players is None:
        players = all_players
    else:
        if not players:
            players = []
        else:
            players = [model.get_player(s, p) for p in players]
        if extra_player_pages:
            extra_players = model.get_old_player_pages(s, extra_player_pages)
            players.extend(p for p in extra_players if p not in players)
    # Randomise order
    random.shuffle(players)

    setup_website_dir(env, WEBSITE_DIR, all_players)

    write_index(s, env)

    write_404(env)

    write_streaks(s, env)

    write_highscores(s, env)

    write_player_pages(s, env, players)

    write_player_api(s, env, players)

    print("Wrote website in %s seconds" % round(time.time() - start, 2))
