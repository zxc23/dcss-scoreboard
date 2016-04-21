"""Utility functions for website generation."""

import datetime


import dateutil.parser

from . import model
from . import modelutils


def prettyint(value):
    """Jinja filter to prettify ints.

    eg, 1234567 to '1,234,567'.
    """
    return "{0:,}".format(value)


def prettydur(duration):
    """Jinja filter to convert seconds to a pretty duration.

    eg, 170 to '2 minutes, 50 seconds'.
    """
    if type(duration) != int:
        duration = int(duration)
    return str(datetime.timedelta(seconds=duration))


def prettycounter(counter):
    """Jinja filter to convert a counter dict to pretty text.

    Sorts by lexical order of keys.

    eg, {'c':1, 'b': 3, 'a': 2} to 'a (2), c (1), b (3)'.
    """
    return ", ".join("{open}{k} ({v}){close}".format(
        k=k,
        v=v,
        open="" if v > 0 else '<span class="text-muted">',
        close="" if v > 0 else '</span>')
                     for k, v in sorted(counter.items(),
                                        key=lambda i: i[0]))


def prettycrawldate(d):
    """Jinja filter to convert crawl date string to pretty text."""
    return modelutils.crawl_date_to_datetime(d).strftime('%c')


def prettydate(d):
    """Jinja filter to convert datetime object to pretty text."""
    return d.strftime('%c')


def gametotablerow(game, prefix_row=None, show_player=False):
    """Jinja filter to convert a game row to a table row."""
    t = """<tr class="{win}">
      {prefix_row}
      {player_row}
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

    return t.format(
        win='table-success' if game.ktyp == 'winning' else 'table-danger'
        if game.ktyp == 'quitting' else '',
        prefix_row='' if prefix_row is None else "<td>%s</td>" % game.raw_data.get(
            prefix_row),
        player_row='' if not show_player else
            "<td><a href='players/{name}.html'>{name}</a></td>".format(name=game.name),
        score=prettyint(game.raw_data['sc']),
        character=game.raw_data['char'],
        place=game.raw_data['place'],
        end=game.raw_data.get('tmsg', ''),  # Older logfiles don't have this
        xl=game.raw_data['xl'],
        turns=prettyint(game.raw_data['turn']),
        duration=prettydur(game.raw_data['dur']),
        runes=game.raw_data.get('nrune', '0'),
        date=prettydate(game.end),
        version=game.raw_data['v'])


def streaktotablerow(streak):
    """Jinja filter to convert a streak to a table row."""
    return """<tr>
      <td>{wins}</td>
      <td><a href="players/{player}.html">{player}<a></td>
      <td>{games}</td>
      <td>{start}</td>
      <td>{end}</td>
      <td>{versions}</td>
    </tr>""".format(
        wins=len(streak['wins']),
        player=streak['player'],
        games=', '.join(model.game(g).char for g in streak['wins']),
        start=prettydate(dateutil.parser.parse(streak['start'])),
        end=prettydate(dateutil.parser.parse(streak['end'])),
        versions=', '.join(sorted(set(model.game(g).v for g in streak['wins']))))


def longeststreaktotablerow(streak):
    """Jinja filter to convert a streak to a table row."""
    return """<tr>
      <td>{wins}</td>
      <td><a href="players/{player}.html">{player}<a></td>
      <td>{games}</td>
      <td>{start}</td>
      <td>{end}</td>
      <td>{versions}</td>
      <td>{streak_breaker}</td>
    </tr>""".format(
        wins=len(streak['wins']),
        player=streak['player'],
        games=', '.join(model.game(g).char for g in streak['wins']),
        start=prettydate(dateutil.parser.parse(streak['start'])),
        end=prettydate(dateutil.parser.parse(streak['end'])),
        versions=', '.join(sorted(set(model.game(g).v for g in streak['wins']))),
        streak_breaker=model.game(streak['streak_breaker']).char if 'streak_breaker' in streak else '')
