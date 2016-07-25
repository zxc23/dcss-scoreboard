"""Utility functions for website generation."""

import datetime

import jinja2

import scoreboard.model as model
import scoreboard.modelutils as modelutils
import scoreboard.constants as const

PRETTY_TIME_FORMAT = '%-d %B %Y'
TIME_FORMAT = '<time class="timeago" datetime="{ts}Z">{t}</time>'


def prettyint(value):
    """Jinja filter to prettify ints.

    eg, 1234567 to '1,234,567'.
    """
    return "{0:,}".format(value)


def prettydur(duration, hours=False):
    """Jinja filter to convert duration in seconds to a pretty "HH:MM:SS".

    Parameters:
        duration: (int) duration in seconds
        hours (bool) Convert to only hours (with a minimum of 1 -- for player
            'hours played' metric).

    Examples:
        prettydur(170) => '0:2:50'
        prettydur(0, hours=True) => '1'
        prettydur(86400, hours=True) => '24'
    """
    if type(duration) != int:
        duration = int(duration)
    delta = datetime.timedelta(seconds=duration)
    if hours:
        dur = delta.total_seconds() / 3600
        return str(int(dur)) if dur > 1 else '1'
    else:
        return str(delta)


def prettycounter(d):
    """Jinja filter to convert an ordered dict to pretty text.
    eg, {'c':1, 'b': 3, 'a': 2} to 'a (2), c (1), b (3)'.
    """
    return ", ".join("{open}{k}&nbsp;({v}){close}".format(
        k=k.name.replace(' ', '&nbsp;'),
        v=len(v),
        open="" if len(v) > 0 else '<span class="text-muted">',
        close="" if len(v) > 0 else '</span>') for k, v in d.items())


def prettycrawldate(d):
    """Jinja filter to convert crawl date string to pretty text."""
    d = modelutils.crawl_date_to_datetime(d)
    return prettydate(d)


def prettydate(d):
    """Jinja filter to convert datetime object to pretty text."""
    return TIME_FORMAT.format(ts=d.isoformat(),
                              t=d.strftime(PRETTY_TIME_FORMAT))


def link_player(player, urlbase):
    """Convert a player name into a link."""
    return "<a href='{base}/players/{name}.html'>{name}</a>".format(
        base=urlbase, name=player)


def _games_to_table(env,
                    games,
                    *,
                    prefix_col=None,
                    prefix_col_title=None,
                    show_player=False,
                    winning_games=False,
                    skip_header=False):
    """Jinja filter to convert a list of games into a standard table.

    Parameters:
        env: Environment -- passed in automatically
        prefix_col (func): Function to return prefix column's value. Passed each game.
        prefix_col_title (str): Title for the prefix_col column
        show_player (bool): Show the player name column
        winning_games (bool): The table has only winning games, so don't show
                              place or end columns, and do show runes.
        skip_header (bool): Skip the header?

    Returns: (string) '<table>contents</table>'.
    """

    def format_trow(game):
        """Convert a game to a table row."""
        return trow.format(
            win='table-success' if game.won else '',
            prefix_col=''
            if not prefix_col else "<td>%s</td>" % prefix_col(game),
            player_row='' if not show_player else "<td>%s</td>" %
            link_player(game.account.player.name, env.globals['urlbase']),
            score=prettyint(game.score),
            character="{}{}".format(game.species.short, game.background.short),
            god=game.god.name,
            place=""
            if winning_games else "<td>%s</td>" % game.place.as_string,
            end="" if winning_games else "<td>%s</td>" % game.tmsg,
            turns=prettyint(game.turn),
            duration=prettydur(game.dur),
            date=prettydate(game.end),
            version=game.version.v,
            morgue=morgue_link(game))

    t = """<table class="{classes}">
          <thead>
            <tr>
            {thead}
            </tr>
          </thead>
          <tbody>
            {tbody}
          </tbody>
        </table>"""

    thead = """{prefix}
              {player}
              <th class="text-xs-right">Score</th>
              <th>Combo</th>
              <th>God</th>
              {place}
              {end}
              <th class="text-xs-right">Turns</th>
              <th class="text-xs-right">Duration</th>
              <th class="text-xs-right">Date</th>
              <th>Version</th>
              <th>Morgue</th>""".format(
        prefix='' if not prefix_col else '<th>%s</th>' % prefix_col_title,
        player='' if not show_player else '<th>Player</th>',
        place='' if winning_games else '<th>Place</th>',
        end='' if winning_games else '<th>End</th>')

    trow = """<tr>
      {prefix_col}
      {player_row}
      <td class="text-xs-right">{score}</td>
      <td>{character}</td>
      <td>{god}</td>
      {place}
      {end}
      <td class="text-xs-right">{turns}</td>
      <td class="text-xs-right">{duration}</td>
      <td class="text-xs-right">{date}</td>
      <td>{version}</td>
      <td>{morgue}</td>
    </tr>"""

    tbody = "\n".join(format_trow(game) for game in games)

    return t.format(classes=const.TABLE_CLASSES,
                    thead=thead if not skip_header else '',
                    tbody=tbody)


def streakstotable(streaks, show_player=True, show_loss=True, limit=None):
    """Jinja filter to convert a list of streaks into a standard table.

    Parameters:
        streaks: list of streaks
        show_player (bool): Show the player name column.
        show_loss (bool): Show the losing game column.
        limit (int): The table won't display more games than this.

    Returns: (string) '<table>contents</table>'.
    """

    def format_trow(streak, show_player, show_loss):
        """Convert a streak to a table row."""
        player = ""
        loss = ""
        if show_player:
            player = "<td><a href='players/{player}.html'>{player}<a></td>".format(
                player=streak.player.name)
        if show_loss:
            loss = "<td>%s</td>" % streak.breaker.char

        games_list = ', '.join(morgue_link(g, g.char) for g in streak.games)
        start_date = prettydate(streak.games[0].start)
        end_date = prettydate(streak.games[-1].end)

        return trow.format(
            wins=len(streak.games),
            player=player,
            games=games_list,
            start=start_date,
            end=end_date,
            streak_breaker=loss)

    t = """<table class="{classes}">
          <thead>
            <tr>
            {thead}
            </tr>
          </thead>
          <tbody>
            {tbody}
          </tbody>
        </table>"""

    thead = """<th class="text-xs-right">Wins</th>
               {player}
               <th>Games</th>
               <th class="date-table-col text-xs-right">First Win</th>
               <th class="date-table-col text-xs-right">Last Win</th>
               {loss}""".format(player=''
                                if not show_player else '<th>Player</th>',
                                loss='' if not show_loss else '<th>Loss</th>')

    trow = """<tr>
        <td class="text-xs-right">{wins}</td>
        {player}
        <td>{games}</td>
        <td class="text-xs-right">{start}</td>
        <td class="text-xs-right">{end}</td>
        {streak_breaker}
        </tr>"""

    if limit:
        streaks = streaks[:limit]

    return t.format(classes=const.TABLE_CLASSES,
                    thead=thead,
                    tbody="\n".join(format_trow(streak, show_player, show_loss)
                                    for streak in streaks))


def mosthighscorestotable(highscores):
    """Jinja filter to convert a list of combo highscores by players into a standard table."""
    table = """<table class="{classes}">
          <thead>
            <tr>
              <th>Player</th>
              <th class="text-xs-right">Highscores</th>
              <th>Combos</th>
            </tr>
          </thead>
          <tbody>
            {tbody}
          </tbody>
        </table>"""

    tbody = ""

    for entry in highscores:
        player = entry[0]
        games = entry[1]
        combos = ', '.join([morgue_link(game, game.char) for game in games])
        tbody += ("""<tr>
                       <td>%s</td>
                       <td class="text-xs-right">%s</td>
                       <td>%s</td>
                     </tr>""" %
                  ("<a href='players/{player}.html'>{player}<a>".format(
                      player=player), len(games), combos))

    return table.format(classes=const.TABLE_CLASSES, tbody=tbody)


def recordsformatted(records):
    result = """{race}
                {role}
                {god}
                {combo}"""

    race = ''
    role = ''
    god = ''
    combo = ''

    if records['race']:
        race = "<p><strong>Species (%s):</strong> %s</p>" % (
            len(records['race']), ', '.join([morgue_link(game, game.rc)
                                             for game in records['race']]))

    if records['role']:
        role = "<p><strong>Backgrounds (%s):</strong> %s</p>" % (
            len(records['role']), ', '.join([morgue_link(game, game.bg)
                                             for game in records['role']]))

    if records['god']:
        god = "<p><strong>Gods (%s):</strong> %s</p>" % (
            len(records['god']), ', '.join([morgue_link(game, game.god)
                                            for game in records['god']]))

    if records['combo']:
        combo = "<p><strong>Combos (%s):</strong> %s</p>" % (
            len(records['combo']), ', '.join([morgue_link(game, game.char)
                                              for game in records['combo']]))

    return result.format(race=race, role=role, god=god, combo=combo)


def morgue_link(game, text="Morgue"):
    """Returns a hyperlink to a morgue file.

    Game can be either a gid string or a game object.
    """
    return "<a href='" + modelutils.morgue_url(game) + "'>" + str(
        text) + "</a>"


def percentage(n, digits=2):
    """Convert a number from 0-1 to a percentage."""
    return "%s" % round(n*100, digits)


def shortest_win(games):
    """Given a list of games, return the win which is the shortest (turns)."""
    wins = filter(lambda g: g.won, games)
    return min(wins, key=lambda g: g.dur)


def fastest_win(games):
    """Given a list of games, return the win which is the fastest (time)."""
    wins = filter(lambda g: g.won, games)
    return min(wins, key=lambda g: g.turn)


def highscore(games):
    """Given a list of games, return the highest scoring game."""
    return max(games, key=lambda g: g.score)


@jinja2.environmentfilter
def generic_games_to_table(env, data):
    return _games_to_table(env, data, show_player=False, winning_games=False)


@jinja2.environmentfilter
def generic_highscores_to_table(env, data, show_player=True):
    return _games_to_table(
        env, data, show_player=show_player,
        winning_games=True)


@jinja2.environmentfilter
def species_highscores_to_table(env, data):
    return _games_to_table(env,
                           data,
                           show_player=True,
                           prefix_col=lambda g: g.species.name,
                           prefix_col_title='Species',
                           winning_games=True)


@jinja2.environmentfilter
def background_highscores_to_table(env, data):
    return _games_to_table(env,
                           data,
                           show_player=True,
                           prefix_col=lambda g: g.background.name,
                           prefix_col_title='Background',
                           winning_games=True)
