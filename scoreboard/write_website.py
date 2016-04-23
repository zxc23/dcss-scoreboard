"""Take generated score data and write out all website files."""

import os
import json
import time
import shutil
import jsmin

import jinja2

from . import model, webutils
from . import constants as const


def jinja_env():
    """Create the Jinja template environment."""
    template_path = os.path.join(os.path.dirname(__file__), 'html_templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters['prettyint'] = webutils.prettyint
    env.filters['prettydur'] = webutils.prettydur
    env.filters['prettycounter'] = webutils.prettycounter
    env.filters['prettycrawldate'] = webutils.prettycrawldate
    env.filters['gametotablerow'] = webutils.gametotablerow
    env.filters['streaktotablerow'] = webutils.streaktotablerow
    env.filters['longeststreaktotablerow'] = webutils.longeststreaktotablerow
    env.filters['prettydate'] = webutils.prettydate
    env.filters['gidtogame'] = model.game

    env.globals['urlbase'] = const.WEBSITE_URLBASE
    env.globals['tableclasses'] = "table table-hover table-striped"
    return env


def achievement_data(ordered=False):
    """Load achievement data.

    If ordered is True, the achievements are returned as a list in display
    order, otherwise they are returned as a dict keyed off the achievement ID.
    """
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    return json.load(open(path))


def write_player_stats(player, stats, outfile, achievements, global_stats,
                       streaks, active_streaks, highscores, template):
    """Write stats page for an individual player."""
    stats['wins'] = stats['wins'][-5:]
    recent_games = model.recent_games(player=player)
    records = highscores.get(player, {})
    streaks = [s for s in streaks if s['player'] == player]
    active_streak = global_stats['active_streaks'].get(player)
    with open(outfile, 'w') as f:
        f.write(template.render(player=player,
                                stats=stats,
                                achievement_data=achievements,
                                const=const,
                                records=records,
                                streaks=streaks,
                                active_streak=active_streak,
                                recent_games=recent_games))


def write_website(rebuild=True, players=[]):
    """Write all website files.

    Paramers:
        rebuild (bool) If True, recreate the website from scratch
        players (list of strings) Only rebuild these players (if rebuild=False)
    """
    start = time.time()
    env = jinja_env()
    all_players = sorted(model.all_player_names())

    if rebuild:
        players = all_players
        print("Writing HTML to %s" % const.WEBSITE_DIR)
        if os.path.isdir(const.WEBSITE_DIR):
            print("Clearing %s" % const.WEBSITE_DIR)
            shutil.rmtree(const.WEBSITE_DIR)
        os.mkdir(const.WEBSITE_DIR)

        print("Copying static assets")
        src = os.path.join(os.path.dirname(__file__), 'html_static')
        dst = os.path.join(const.WEBSITE_DIR, 'static')
        shutil.copytree(src, dst)
        print("Generating static player list")
        with open(os.path.join(dst, 'js', 'players.json'), 'w') as f:
            f.write(json.dumps(all_players))

    print("Loading scoring data")
    # Get stats
    stats = model.global_stats()
    overall_highscores = model.highscores()
    race_highscores = model.race_highscores()
    role_highscores = model.role_highscores()
    god_highscores = model.god_highscores()
    combo_highscores = model.combo_highscores()
    fastest_wins = model.fastest_wins()
    shortest_wins = model.shortest_wins()
    recent_wins = model.recent_games(wins=True)

    # I'm not proud of this block of code, but it works
    # Create a list of [(name, [streak_chars]), ...] for the index
    inverted_combo_highscores = {}
    for entry in combo_highscores:
        if entry.name not in inverted_combo_highscores:
            inverted_combo_highscores[entry.name] = [entry.char]
        else:
            inverted_combo_highscores[entry.name].append(entry.char)
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

    print("Writing index")
    with open(os.path.join(const.WEBSITE_DIR, 'index.html'), 'w') as f:
        template = env.get_template('index.html')
        f.write(template.render(recent_wins=recent_wins,
                                active_streaks=sorted_active_streaks,
                                combo_high_scores=inverted_combo_highscores))

    print("Writing minified local JS")
    scoreboard_path = os.path.join(const.WEBSITE_DIR,
                                   'static/js/dcss-scoreboard.js')
    with open(scoreboard_path, 'w') as f:
        template = env.get_template('dcss-scoreboard.js')
        f.write(jsmin.jsmin(template.render()))

    print("Writing streaks")
    with open(os.path.join(const.WEBSITE_DIR, 'streaks.html'), 'w') as f:
        template = env.get_template('streaks.html')
        f.write(template.render(streaks=sorted_streaks,
                                active_streaks=sorted_active_streaks))

    print("Writing highscores")
    with open(os.path.join(const.WEBSITE_DIR, 'highscores.html'), 'w') as f:
        template = env.get_template('highscores.html')
        f.write(template.render(overall_highscores=overall_highscores,
                                race_highscores=race_highscores,
                                role_highscores=role_highscores,
                                god_highscores=god_highscores,
                                combo_highscores=combo_highscores,
                                fastest_wins=fastest_wins,
                                shortest_wins=shortest_wins))

    print("Writing player pages... ")
    player_html_path = os.path.join(const.WEBSITE_DIR, 'players')
    os.mkdir(player_html_path)
    achievements = achievement_data()
    global_stats = model.global_stats()
    template = env.get_template('player.html')

    player_highscores = {}
    for game in race_highscores:
        player_highscores.get(game.name, {}).get('race_highscores', []).append(game)

    for game in role_highscores:
        player_highscores.get(game.name, {}).get('role_highscores', []).append(game)

    for game in combo_highscores:
        player_highscores.get(game.name, {}).get('combo_highscores', []).append(game)

    for game in god_highscores:
        player_highscores.get(game.name, {}).get('god_highscores', []).append(game)

    n = 0
    for player in players:
        stats = model.get_player_stats(player)
        highscores = player_highscores.get(player, {})

        # Don't make pages for players with no games played
        if stats['games'] == 0:
            continue

        outfile = os.path.join(player_html_path, player + '.html')
        write_player_stats(player, stats, outfile, achievements, global_stats,
                           sorted_streaks, active_streaks, highscores,
                           template)
        n += 1
        if not n % 10000:
            print(n)
    end = time.time()
    print("Wrote website in %s seconds" % round(end - start, 2))


if __name__ == "__main__":
    write_website()
