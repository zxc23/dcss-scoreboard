"""Utility functions for website generation."""

import datetime

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


def gametotablerow(game, prefix_row=None, show_player=False):
    """Jinja filter to convert a game dict to a table row."""
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
        win='table-success' if game['ktyp'] == 'winning' else 'table-danger'
        if game['ktyp'] == 'quitting' else '',
        prefix_row='' if prefix_row is None else "<td>%s</td>" % game.get(
            prefix_row),
        player_row='' if not show_player else (
            "<td><a href='players/%s.html'>%s</a></td>" % (game['name'], game[
                'name'])),
        score=prettyint(game['sc']),
        character=game['char'],
        place=game['place'],
        end=game.get('tmsg', ''),  # Older logfiles don't have this line
        xl=game['xl'],
        turns=prettyint(game['turn']),
        duration=prettydur(game['dur']),
        runes=game.get('nrune', ''),  # Older logfiles don't have this line
        date=modelutils.prettycrawldate(game['end']),
        version=game['v'])


def streaktotablerow(streak):
    """Jinja filter to convert a streak to a table row."""
    return """<tr>
      <td>{wins}</td>
      <td><a href="players/{player}.html">{player}<a></td>
      <td>{games}</td>
      <td>{versions}</td>
    </tr>""".format(wins=len(streak),
                    player=streak[0]['name'],
                    games=', '.join(g['char'] for g in streak),
                    versions=', '.join(sorted(set(g['v'] for g in streak))))


def completedstreaktotablerow(streak):
    """Jinja filter to convert a streak to a table row."""
    return """<tr>
      <td>{wins}</td>
      <td><a href="players/{player}.html">{player}<a></td>
      <td>{games}</td>
      <td>{ended}</td>
      <td>{lost_game}</td>
      <td>{versions}</td>
    </tr>""".format(
        wins=len(streak['wins']),
        player=streak['wins'][0]['name'],
        games=', '.join(g['char'] for g in streak['wins']),
        ended=modelutils.prettycrawldate(streak['end']),
        lost_game=streak['streak_breaker']['char'],
        versions=', '.join(sorted(set(g['v'] for g in streak['wins']))))
