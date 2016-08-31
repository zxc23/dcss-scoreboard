"""Take generated score data and write out all website files."""

import os
import json
import time
import datetime
import subprocess
import collections

from typing import Iterable

import jsmin
import jinja2

from . import model
from . import webutils
from . import orm
from . import constants as const

WEBSITE_DIR = 'website'


def _write_file(*, path: str, data: str) -> None:
    """Write a file."""
    with open(path, 'w', encoding='utf8') as f:
        f.write(data)


def jinja_env(urlbase, s):
    """Create the Jinja template environment."""
    template_path = os.path.join(os.path.dirname(__file__), 'html_templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters['prettyint'] = webutils.prettyint
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


def achievement_data():
    """Load achievement data.

    If ordered is True, the achievements are returned as a list in display
    order, otherwise they are returned as a dict keyed off the achievement ID.
    """
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    return json.load(open(path))


def setup_website_dir(env, path, all_players):
    """Create the website dir and add static content."""
    print("Writing HTML to %s" % path)
    if not os.path.exists(path):
        print("mkdir %s/" % path)
        os.mkdir(path)

    print("Copying static assets")
    src = os.path.join(os.path.dirname(__file__), 'html_static')
    dst = os.path.join(path, 'static')
    subprocess.run(['rsync', '-a', src + '/', dst + '/'])

    print("Generating player list")
    _write_file(
        path=os.path.join(dst, 'js', 'players.json'),
        data=json.dumps([p.name for p in all_players]))

    print("Writing minified local JS")
    js_template = env.get_template('dcss-scoreboard.js')
    _write_file(
        path=os.path.join(WEBSITE_DIR, 'static/js/dcss-scoreboard.js'),
        data=jsmin.jsmin(js_template.render()))


def render_index(s, template):
    """Render the index page."""
    return template.render(
        recent_wins=model.list_games(
            s, winning=True, limit=const.FRONTPAGE_TABLE_LENGTH),
        active_streaks=[],
        overall_highscores=model.highscores(
            s, limit=const.FRONTPAGE_TABLE_LENGTH),
        combo_high_scores=model.combo_highscore_holders(
            s, limit=const.FRONTPAGE_TABLE_LENGTH))


def write_index(s, env):
    """Write the index page."""
    print("Writing index")
    template = env.get_template('index.html')
    data = render_index(s, template)
    _write_file(path=os.path.join(WEBSITE_DIR, 'index.html'), data=data)


def write_streaks(s, env):
    """Write the streak page."""
    print("Writing streaks")
    template = env.get_template('streaks.html')
    active_streaks = model.get_streaks(s, active=True, max_age=365)
    best_streaks = model.get_streaks(s, limit=10)
    _write_file(
        path=os.path.join(WEBSITE_DIR, 'streaks.html'),
        data=template.render(
            active_streaks=active_streaks, best_streaks=best_streaks))


def render_highscores(s, template):
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


def write_highscores(s, env):
    """Write the highscores page."""
    print("Writing highscores")
    template = env.get_template('highscores.html')
    data = render_highscores(s, template)
    _write_file(path=os.path.join(WEBSITE_DIR, 'highscores.html'), data=data)


def _get_player_records(global_records, player):
    out = {}  # type: dict
    for typ, games in global_records.items():
        for game in games:
            if game.player.name == player:
                if typ not in out:
                    out[typ] = [game]
                else:
                    out[typ].append(game)
    return out


def _wins_per_species(s, games: Iterable[orm.Game]) -> Iterable[orm.Game]:
    """Return a dict of form {<Species 'Ce'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for sp in model.list_species(s, playable=True):
        out[sp] = [g for g in games if g.won and g.species == sp]
    return out


def _wins_per_background(s, games: Iterable[orm.Game]) -> Iterable[orm.Game]:
    """Return a dict of form {<Background 'Be'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for bg in model.list_backgrounds(s, playable=True):
        out[bg] = [g for g in games if g.won and g.background == bg]
    return out


def _wins_per_god(s, games: Iterable[orm.Game]) -> Iterable[orm.Game]:
    """Return a dict of form {<God 'Beogh'>: [winning_game, ...}, ...}."""
    out = collections.OrderedDict()  # type: dict
    for god in model.list_gods(s, playable=True):
        out[god] = [g for g in games if g.won and g.god == god]
    return out


def render_player_page(s, template, player: orm.Player, global_records:
                       dict) -> str:
    """Render an individual player's page."""
    games = model.list_games(s, player=player)
    # Don't make pages for players with no games played
    if len(games) == 0:
        return ''

    records = _get_player_records(global_records, player)
    species_wins = _wins_per_species(s, games)
    background_wins = _wins_per_background(s, games)
    god_wins = _wins_per_god(s, games)
    active_streak = model.get_player_streak(s, player)

    return template.render(
        player=player,
        games=games,
        records=records,
        species_wins=species_wins,
        background_wins=background_wins,
        god_wins=god_wins,
        active_streak=active_streak)


def write_player_page(player_html_path: str, name: str, data: str) -> None:
    """Write an individual player's page."""
    _write_file(path=os.path.join(player_html_path, name + '.html'), data=data)


def write_player_pages(s, env, players):
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
        write_player_page(player_html_path, player.name, data)
        n += 1
        if not n % 100:
            print(n)
    end = time.time()
    print("Wrote player pages in %s seconds" % round(end - start2, 2))


def write_website(players, urlbase=None):
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

    all_players = sorted(model.list_players(s), key=lambda p: p.name)
    if players is None:
        players = all_players
    elif not players:
        players = []
    else:
        players = [model.get_player(s, p) for p in players]

    setup_website_dir(env, WEBSITE_DIR, all_players)

    write_index(s, env)

    write_streaks(s, env)

    write_highscores(s, env)

    write_player_pages(s, env, players)

    print("Wrote website in %s seconds" % round(time.time() - start, 2))
