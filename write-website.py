#!/usr/bin/env python3

import os
import json
import datetime
import time

import jinja2

OUTDIR = 'dcss-scoreboard-html'

def prettyint(value):
    """Jinja filter to prettify ints.

    eg, 1234567 to '1 234 567'.
    """
    return "{0:,}".format(value)

def prettydur(duration):
    """Jinja filter to convert seconds to a pretty duration.

    eg, 170 to '2 minutes, 50 seconds'.
    """
    return str(datetime.timedelta(seconds=duration))

def prettycounter(counter, reverse=True):
    """Jinja filter to convert a counter dict to pretty text.

    Set reverse=False to sort ascending instead of descending.

    eg, {'a':1, 'b': 3, 'c': 2} to 'a (3), c (2), b (1)'.
    """
    return ", ".join("{k} ({v})".format(k=k, v=v) for k, v in sorted(counter.items(), key=lambda i: i[1], reverse=reverse))

def prettycrawldate(d):
    """Jinja filter to convert crawl logfile date to pretty text."""
    try:
        return time.strftime("%c", time.strptime(d, "%Y%m%d%H%M%SS"))
    except ValueError:
        return d

def gametotablerow(game):
    """Jinja filter to convert a game dict to a table row."""
    return """<tr {win}>
      <td>{score}</td>
      <td>{character}</td>
      <td>{place}</td>
      <td>{end}</td>
      <td>{xl}</td>
      <td>{turns}</td>
      <td>{duration}</td>
      <td>{runes}</td>
      <td>{date}</td>
      <td>{version}</td>
    </tr>""".format(win='class="table-success"' if game['ktyp'] == 'winning' else 'class="table-danger"' if game['ktyp'] == 'quitting' else '',
                    score=game['sc'],
                    character=game['char'],
                    place=game['place'],
                    end=game['tmsg'],
                    xl=game['xl'],
                    turns=game['turn'],
                    duration=game['dur'],
                    runes='?',
                    date=prettycrawldate(game['end']),
                    version=game['v'])


if __name__ == '__main__':
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('html_templates'))
    env.filters['prettyint'] = prettyint
    env.filters['prettydur'] = prettydur
    env.filters['prettycounter'] = prettycounter
    env.filters['prettycrawldate'] = prettycrawldate
    env.filters['gametotablerow'] = gametotablerow

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
