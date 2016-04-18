#!/usr/bin/env python3
"""Take generated score data and write out all website files."""

import os
import sys
import json
import jinja2
import time

from . import model
from . import webutils

OUTDIR = 'website'


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
    env.filters['completedstreaktotablerow'] = webutils.completedstreaktotablerow
    return env


def achievement_data():
    """Load achievement data."""
    path = os.path.join(os.path.dirname(__file__), 'achievements.json')
    return json.load(open(path))


def write_website():
    """Write all website files."""
    env = jinja_env()

    print("Writing HTML to %s" % OUTDIR)
    if not os.path.isdir(OUTDIR):
        os.mkdir(OUTDIR)

    print("Writing index")
    with open(os.path.join(OUTDIR, 'index.html'), 'w') as f:
        template = env.get_template('index.html')
        f.write(template.render())

    print("Writing highscores")
    with open(os.path.join(OUTDIR, 'highscores.html'), 'w') as f:
        template = env.get_template('highscores.html')
        f.write(template.render(stats=model.get_all_global_scores()))

    print("Writing streaks")
    with open(os.path.join(OUTDIR, 'streaks.html'), 'w') as f:
        template = env.get_template('streaks.html')
        f.write(template.render(stats=model.get_all_global_scores()))

    print("Writing players")
    player_html_path = os.path.join(OUTDIR, 'players')
    if not os.path.isdir(player_html_path):
        os.mkdir(player_html_path)
    players = sorted(model.players())
    with open(os.path.join(OUTDIR, 'players.html'), 'w') as f:
        template = env.get_template('players.html')
        f.write(template.render(players=players))

    start = time.time()
    print("Writing player pages... ", end='')
    sys.stdout.flush()
    achievements = achievement_data()
    template = env.get_template('player.html')
    for row in model.player_scores():
        outfile = os.path.join(player_html_path, row.name + '.html')
        with open(outfile, 'w') as f:
            f.write(template.render(player=row.name,
                                    stats=row.scoringinfo,
                                    achievement_data=achievements))
    end = time.time()
    print("done in %s seconds" % round(end - start, 2))


if __name__ == "__main__":
    write_website()
