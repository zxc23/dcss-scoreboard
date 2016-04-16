#!/usr/bin/env python3

import os
import json
import datetime

import jinja2

OUTDIR = 'dcss-scoreboard-html'


def prettyint(value):
    """Jinja filter to prettify ints.

    eg, 1234567 to '1,234,567'.
    """
    return "{0:,}".format(value)


def prettydur(duration):
    """Jinja filter to convert seconds to a pretty duration.

    eg, 170 to '2 minutes, 50 seconds'.
    """
    return str(datetime.timedelta(seconds=duration))


def prettycounter(counter):
    """Jinja filter to convert a counter dict to pretty text.

    Sorts by lexical order of keys.

    eg, {'c':1, 'b': 3, 'a': 2} to 'a (2), c (1), b (3)'.
    """
    return ", ".join("{k} ({v})".format(k=k,
                                        v=v)
                     for k, v in sorted(counter.items(), key=lambda i: i[0]))


def prettycrawldate(d):
    """Jinja filter to convert crawl logfile date to pretty text.

    Note: crawl dates use a 0-indexed month... I think you can blame struct_tm
    for this.
    """
    # Increment the month by one
    d = d[:4] + '%02d' % (int(d[4:6]) + 1) + d[6:]
    try:
        return datetime.datetime(year=int(d[:4]),
                                 month=int(d[4:6]),
                                 day=int(d[6:8]),
                                 hour=int(d[8:10]),
                                 minute=int(d[10:12]),
                                 second=int(d[12:14])).strftime("%c")

    except ValueError:
        return d


def gametotablerow(game, prefix_row=None):
    """Jinja filter to convert a game dict to a table row."""
    t = """<tr class="{win}">
      {prefix_row}
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
    </tr>"""
    return t.format(win='table-success' if game['ktyp'] == 'winning' else
                        'table-danger' if game['ktyp'] == 'quitting' else '',
                    prefix_row='' if prefix_row is None else "<td>%s</td>" % game[prefix_row],
                    score=prettyint(game['sc']),
                    character=game['char'],
                    place=game['place'],
                    end=game['tmsg'],
                    xl=game['xl'],
                    turns=prettyint(game['turn']),
                    duration=prettydur(game['dur']),
                    runes='?',
                    date=prettycrawldate(game['end']),
                    version=game['v'])

def streaktotablerow(streak):
    """Jinja filter to convert a streak to a table row."""
    return """<tr>
      <td>{wins}</td>
      <td>{player}</td>
      <td>{games}</td>
      <td>{versions}</td>
    </tr>""".format(wins=len(streak),
                    player=streak[0]['name'],
                    games=', '.join(g['char'] for g in streak),
                    versions=', '.join(sorted(set(g['v'] for g in streak))))


def main():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('html_templates'))
    env.filters['prettyint'] = prettyint
    env.filters['prettydur'] = prettydur
    env.filters['prettycounter'] = prettycounter
    env.filters['prettycrawldate'] = prettycrawldate
    env.filters['gametotablerow'] = gametotablerow
    env.filters['streaktotablerow'] = streaktotablerow

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
        f.write(template.render(stats=data['global_stats']))

    print("Writing players")
    player_html_path = os.path.join(OUTDIR, 'players')
    if not os.path.isdir(player_html_path):
        os.mkdir(player_html_path)
    players = sorted(data['players'].keys(), key=lambda s: s.lower())
    with open(os.path.join(OUTDIR, 'players.html'), 'w') as f:
        template = env.get_template('players.html')
        f.write(template.render(players=players))

    print("Writing player pages")
    template = env.get_template('player.html')
    for player, stats in data['players'].items():
        outfile = os.path.join(player_html_path, player + '.html')
        with open(outfile, 'w') as f:
            f.write(template.render(player=player, stats=stats))


if __name__ == '__main__':
    main()
