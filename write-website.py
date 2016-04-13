#!/usr/bin/env python3

import os
import json
import datetime

import jinja2

OUTDIR = 'dcss-scoreboard-html'

def prettyint(value):
    """Jinja filter to prettify ints.

    eg, 1234567 to '1 234 567'.
    """
    return "{0:,}".format(int(value))

def prettydur(duration):
    """Jinja filter to convert seconds to a pretty duration.

    eg, 170 to '2 minutes, 50 seconds'.
    """
    return str(datetime.timedelta(seconds=int(duration)))

def prettycounter(counter, reverse=True):
    """Jinja filter to convert a counter dict to pretty text.

    Set reverse=False to sort ascending instead of descending.

    eg, {'a':1, 'b': 3, 'c': 2} to 'a (3), c (2), b (1)'.
    """
    return ", ".join("{k} ({v})".format(k=k, v=v) for k, v in sorted(counter.items(), key=lambda i: i[1], reverse=reverse))

if __name__ == '__main__':
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('html_templates'))
    env.filters['prettyint'] = prettyint
    env.filters['prettydur'] = prettydur
    env.filters['prettycounter'] = prettycounter

    data = json.loads(open('scoring_data.json').read())

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
        f.write(template.render(highscores=data['global_stats']))

    print("Writing players")
    player_html_path = os.path.join(OUTDIR, 'players')
    if not os.path.isdir(player_html_path):
        os.mkdir(player_html_path)
    players = sorted(data['players'].keys(), key=lambda s: s.lower())
    with open(os.path.join(OUTDIR, 'players.html'), 'w') as f:
        template = env.get_template('players.html')
        f.write(template.render(players=players))

    for player, stats in data['players'].items():
        print("Writing player %s" % player)
        outfile = os.path.join(player_html_path, player + '.html')
        with open(outfile, 'w') as f:
            template = env.get_template('player.html')
            f.write(template.render(player=player, stats=stats))
