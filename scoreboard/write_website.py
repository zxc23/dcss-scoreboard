"""Take generated score data and write out all website files."""

import os
import json
import time
import shutil
import sys

import jinja2

from . import model, webutils, constants

OUTDIR = 'website'
URLBASE = os.path.join(os.getcwd(), 'website')


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
    env.filters[
        'completedstreaktotablerow'] = webutils.completedstreaktotablerow
    env.globals['urlbase'] = URLBASE
    return env


def achievement_data(ordered=False):
    """Load achievement data.

    If ordered is True, the achievements are returned as a list in display
    order, otherwise they are returned as a dict keyed off the achievement ID.
    """
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    return json.load(open(path))


def write_player_stats(player, stats, outfile, achievements, global_stats,
                       streaks, active_streaks, template):
    """Write stats page for an individual player."""
    records = {}
    records['combo'] = sorted(
        [g
         for g in global_stats['char_highscores'].values()
         if g['name'] == player],
        key=lambda x: x['char'])
    records['race'] = sorted(
        [g for g in global_stats['rc_highscores'].values()
         if g['name'] == player],
        key=lambda x: x['char'][:2])
    records['role'] = sorted(
        [g for g in global_stats['bg_highscores'].values()
         if g['name'] == player],
        key=lambda x: x['char'][2:])
    streaks = [s for s in streaks if s['player'] == player]
    active_streak = global_stats['active_streaks'].get(player)
    with open(outfile, 'w') as f:
        f.write(template.render(player=player,
                                stats=stats,
                                achievement_data=achievements,
                                constants=constants,
                                records=records,
                                streaks=streaks,
                                active_streak=active_streak))


def write_website():
    """Write all website files."""
    env = jinja_env()

    print("Writing HTML to %s" % OUTDIR)
    if os.path.isdir(OUTDIR):
        print("Clearing %s" % OUTDIR)
        shutil.rmtree(OUTDIR)
    os.mkdir(OUTDIR)

    print("Copying static assets")
    src = os.path.join(os.path.dirname(__file__), 'html_static')
    dst = os.path.join(OUTDIR, 'static')
    shutil.copytree(src, dst)

    print("Writing index")
    with open(os.path.join(OUTDIR, 'index.html'), 'w') as f:
        template = env.get_template('index.html')
        f.write(template.render())

# Get stats
    stats = model.get_all_global_stats()

    # Merge active streaks into streaks
    streaks = stats['completed_streaks']
    active_streaks = stats['active_streaks']
    sorted_active_streaks = []

    for streak in active_streaks.values():
        if streak['length'] > 1:
            streaks.append(streak)
            sorted_active_streaks.append(streak)

# Sort streaks
    sorted_streaks = sorted(streaks, key=lambda x: (-x['length'], x['end']))
    sorted_active_streaks.sort(key=lambda x: (-x['length'], x['end']))

    print("Writing highscores")
    with open(os.path.join(OUTDIR, 'highscores.html'), 'w') as f:
        template = env.get_template('highscores.html')
        f.write(template.render(stats=stats))
    print("Writing streaks")
    with open(os.path.join(OUTDIR, 'streaks.html'), 'w') as f:
        template = env.get_template('streaks.html')
        f.write(template.render(streaks=sorted_streaks,
                                active_streaks=sorted_active_streaks))

    print("Writing players")
    player_html_path = os.path.join(OUTDIR, 'players')
    if not os.path.isdir(player_html_path):
        os.mkdir(player_html_path)
    players = sorted(model.players())
    with open(os.path.join(OUTDIR, 'players.html'), 'w') as f:
        template = env.get_template('players.html')
        f.write(template.render(players=players))

    start = time.time()
    print("Writing player pages... ")
    achievements = achievement_data()
    global_stats = model.get_all_global_stats()
    template = env.get_template('player.html')
    n = 0
    for row in model.get_all_player_stats():
        # Don't make pages for players with no games played
        if row.stats['games'] == 0:
            continue

        player = row.name
        stats = row.stats
        outfile = os.path.join(player_html_path, player + '.html')
        write_player_stats(player, stats, outfile, achievements, global_stats,
                           sorted_streaks, active_streaks, template)

        n += 1
        if not n % 10000:
            print(n)

    end = time.time()
    print("Done scoring in %s seconds" % round(end - start, 2))

if __name__ == "__main__":
    write_website()
