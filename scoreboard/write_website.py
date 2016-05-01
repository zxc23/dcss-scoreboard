"""Take generated score data and write out all website files."""

import os
import json
import time
import subprocess
import datetime

import jsmin
import jinja2

from . import model, webutils
from . import constants as const

WEBSITE_DIR = 'website'


def jinja_env():
    """Create the Jinja template environment."""
    template_path = os.path.join(os.path.dirname(__file__), 'html_templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters['prettyint'] = webutils.prettyint
    env.filters['prettydur'] = webutils.prettydur
    env.filters['prettycounter'] = webutils.prettycounter
    env.filters['prettycrawldate'] = webutils.prettycrawldate
    env.filters['gamestotable'] = webutils.gamestotable
    env.filters['streakstotable'] = webutils.streakstotable
    env.filters['prettydate'] = webutils.prettydate
    env.filters['gidtogame'] = model.game
    env.filters['link_player'] = webutils.link_player
    env.filters['morgue_link'] = webutils.morgue_link
    env.filters['mosthighscorestotable'] = webutils.mosthighscorestotable
    env.filters['recordsformatted'] = webutils.recordsformatted

    env.globals['tableclasses'] = const.TABLE_CLASSES
    return env


def achievement_data(ordered=False):
    """Load achievement data.

    If ordered is True, the achievements are returned as a list in display
    order, otherwise they are returned as a dict keyed off the achievement ID.
    """
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    return json.load(open(path))


def player_records(player, race_highscores, role_highscores, combo_highscores,
                   god_highscores):
    """Return a dictionary of player records.

    Dict is of the form { 'race': [('Ce', gid), ('Vp', gid)], 'role': [],
        'combo': [...], 'god': [...] }.
    """
    records = {'race': [], 'role': [], 'combo': [], 'god': []}
    for game in race_highscores:
        if game.name == player:
            records['race'].append(game)
    for game in role_highscores:
        if game.name == player:
            records['role'].append(game)
    for game in combo_highscores:
        if game.name == player:
            records['combo'].append(game)
    for game in god_highscores:
        if game.name == player:
            records['god'].append(game)

    return records


def write_player_stats(*, player, stats, outfile, achievements, streaks,
                       active_streak, template, records):
    """Write stats page for an individual player.

    Parameters:
        player (str) Player Name
        stats (dict) Player's stats dict from model.player_stats
        outfile (str) Output filename
        achievements (dict) Player's achievements
        streaks (list) Player's streaks or []
        active_streak (dict) Player's active streak or {}
        template (Jinja template) Template to render with.
        records (dict) Player's global highscores

    Returns: None.
    """
    recent_games = model.recent_games(player=player)
    all_wins = model.recent_games(wins=True, player=player, num=None)
    with open(outfile, 'w', encoding='utf8') as f:
        f.write(template.render(player=player,
                                stats=stats,
                                all_wins=all_wins,
                                achievement_data=achievements,
                                const=const,
                                records=records,
                                streaks=streaks,
                                active_streak=active_streak,
                                recent_games=recent_games))


def write_website(players=set(), urlbase=None):
    """Write all website files.

    Paramers:
        urlbase (str) Base URL for the website
        players (iterable of strings) Only write these player pages.
            If you pass in False, no player pages will be rebuilt.
            If you pass in None, all player pages will be rebuilt.
    """
    start = time.time()

    env = jinja_env()
    if urlbase:
        env.globals['urlbase'] = urlbase
    else:
        env.globals['urlbase'] = os.path.join(os.getcwd(), WEBSITE_DIR)

    all_players = sorted(model.all_player_names())
    if players is None:
        players = all_players
    elif not players:
        players = []

    print("Writing HTML to %s" % WEBSITE_DIR)
    if not os.path.exists(WEBSITE_DIR):
        print("mkdir %s/" % WEBSITE_DIR)
        os.mkdir(WEBSITE_DIR)

    print("Copying static assets")
    src = os.path.join(os.path.dirname(__file__), 'html_static')
    dst = os.path.join(WEBSITE_DIR, 'static')
    subprocess.run(['rsync', '-a', src + '/', dst + '/'])

    print("Generating player list")
    with open(os.path.join(dst, 'js', 'players.json'), 'w') as f:
        f.write(json.dumps(all_players))

    print("Loading scoring data")
    start2 = time.time()
    # Get stats
    stats = model.global_stats()
    overall_highscores = model.highscores()
    race_highscores = model.race_highscores()
    role_highscores = model.role_highscores()
    god_highscores = model.god_highscores()
    combo_highscores = model.combo_highscores()
    fastest_wins = model.fastest_wins()
    shortest_wins = model.shortest_wins()
    recent_wins = model.recent_games(wins=True, num=5)

    # I'm not proud of this block of code, but it works
    # Create a list of [(name, [highscoregame]), ...] for the index
    # It's sorted by number of highscores length
    inverted_combo_highscores = {}
    for entry in combo_highscores:
        if entry.name not in inverted_combo_highscores:
            inverted_combo_highscores[entry.name] = [entry]
        else:
            inverted_combo_highscores[entry.name].append(entry)
    temp = []
    for k, v in inverted_combo_highscores.items():
        temp.append((k, v))
    inverted_combo_highscores = temp
    inverted_combo_highscores = sorted(inverted_combo_highscores,
                                       reverse=True,
                                       key=lambda i: len(i[1]))[:5]

    # Merge active streaks into streaks
    streaks = stats['completed_streaks']
    active_streaks = stats['active_streaks']
    sorted_active_streaks = []

    for streak in active_streaks.values():
        if len(streak['wins']) > 1:
            streaks.append(streak)
            sorted_active_streaks.append(streak)

    # Sort streaks
    sorted_streaks = sorted(streaks, key=lambda s: (-len(s['wins']), s['end']))
    sorted_active_streaks.sort(key=lambda s: (-len(s['wins']), s['end']))

    # Get streaks by player
    player_streaks = {}
    for streak in sorted_streaks:
        if streak['player'] not in player_streaks:
            player_streaks[streak['player']] = [streak]
        else:
            player_streaks[streak['player']].append(streak)

    # Only show streaks active in the past 3 months
    for streak in sorted_active_streaks:
        timedelta = datetime.datetime.now() - model.game(streak['wins'][-
                                                                        1]).end
        if timedelta.days > 90:
            sorted_active_streaks.remove(streak)

    print("Loaded scoring data in %s seconds" % round(time.time() - start, 2))
    print("Writing index")
    with open(
            os.path.join(WEBSITE_DIR, 'index.html'),
            'w',
            encoding='utf8') as f:
        template = env.get_template('index.html')
        f.write(template.render(recent_wins=recent_wins,
                                active_streaks=sorted_active_streaks,
                                overall_highscores=overall_highscores,
                                combo_high_scores=inverted_combo_highscores))

    print("Writing minified local JS")
    scoreboard_path = os.path.join(WEBSITE_DIR, 'static/js/dcss-scoreboard.js')
    with open(scoreboard_path, 'w') as f:
        template = env.get_template('dcss-scoreboard.js')
        f.write(jsmin.jsmin(template.render()))

    print("Writing streaks")
    with open(
            os.path.join(WEBSITE_DIR, 'streaks.html'),
            'w',
            encoding='utf8') as f:
        template = env.get_template('streaks.html')
        f.write(template.render(streaks=sorted_streaks,
                                active_streaks=sorted_active_streaks))

    print("Writing highscores")
    with open(
            os.path.join(WEBSITE_DIR, 'highscores.html'),
            'w',
            encoding='utf8') as f:
        template = env.get_template('highscores.html')
        f.write(template.render(overall_highscores=overall_highscores,
                                race_highscores=race_highscores,
                                role_highscores=role_highscores,
                                god_highscores=god_highscores,
                                combo_highscores=combo_highscores,
                                fastest_wins=fastest_wins,
                                shortest_wins=shortest_wins))

    print("Writing %s player pages... " % len(players))
    start2 = time.time()
    player_html_path = os.path.join(WEBSITE_DIR, 'players')
    if not os.path.exists(player_html_path):
        os.mkdir(player_html_path)
    achievements = achievement_data()
    template = env.get_template('player.html')

    n = 0
    for player in players:
        stats = model.get_player_stats(player)
        streaks = player_streaks.get(player, [])
        active_streak = active_streaks.get(player, {})
        records = player_records(player, race_highscores, role_highscores,
                                 combo_highscores, god_highscores)

        # Don't make pages for players with no games played
        if stats['games'] == 0:
            continue

        outfile = os.path.join(player_html_path, player + '.html')
        write_player_stats(player=player,
                           stats=stats,
                           outfile=outfile,
                           achievements=achievements,
                           streaks=streaks,
                           active_streak=active_streak,
                           template=template,
                           records=records)
        n += 1
        if not n % 10000:
            print(n)
    end = time.time()
    print("Wrote player pages in %s seconds" % round(end - start2, 2))
    print("Wrote website in %s seconds" % round(end - start, 2))


if __name__ == "__main__":
    write_website()
