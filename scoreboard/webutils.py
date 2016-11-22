"""Utility functions for website generation."""

from typing import Iterable, Sequence, Optional, Callable
import datetime  # for typing
import uuid

import jinja2

import scoreboard.modelutils as modelutils
import scoreboard.constants as const
import scoreboard.orm as orm

PRETTY_TIME_FORMAT = '%-d %B %Y'
TIME_FORMAT = '<time class="timeago" datetime="{ts}Z">{t}</time>'


def prettyint(value: int) -> str:
    """Jinja filter to prettify ints.

    eg, 1234567 to '1,234,567'.
    """
    return "{0:,}".format(value)


def prettyhours(duration: int) -> str:
    """Jinja filter to convert duration in seconds to hours (min 1).

    Parameters:
        duration: (int) duration in seconds

    Examples:
        prettyhours(0) => '1'
        prettyhours(86400) => '24'
    """
    if not isinstance(duration, int):
        duration = int(duration)
    return str(duration // 3600) if duration > 3600 else '1'


def prettydur(duration: int) -> str:
    """Jinja filter to convert duration in seconds to a pretty "HH:MM:SS".

    Parameters:
        duration: (int) duration in seconds

    Examples:
        prettydur(170) => '00:02:50'
        prettydur(87000) => '24:10:00'
    """
    if not isinstance(duration, int):
        duration = int(duration)
    return '%02d:%02d:%02d' % (duration // 3600, duration % 3600 // 60,
                               duration % 60)


def prettycounter(d: dict) -> str:
    """Jinja filter to convert an ordered dict to pretty text.
    eg, {'c':1, 'b': 3, 'a': 2} to 'a (2), c (1), b (3)'.
    """
    return ", ".join("{open}{k}&nbsp;({v}){close}".format(
        k=k.name.replace(' ', '&nbsp;'),
        v=len(v),
        open="" if len(v) > 0 else '<span class="text-muted">',
        close="" if len(v) > 0 else '</span>') for k, v in d.items())


def prettycrawldate(d: str) -> str:
    """Jinja filter to convert crawl date string to pretty text."""
    date = modelutils.crawl_date_to_datetime(d)
    return prettydate(date)


def prettydate(d: datetime.datetime) -> str:
    """Jinja filter to convert datetime object to pretty text."""
    return TIME_FORMAT.format(
        ts=d.isoformat(), t=d.strftime(PRETTY_TIME_FORMAT))


def link_player(player: str, urlbase: str) -> str:
    """Convert a player name into a link."""
    return "<a href='{base}/players/{name}.html'>{name}</a>".format(
        base=urlbase, name=player)


def _games_to_table(env: jinja2.environment.Environment,
                    games: Iterable[orm.Game],
                    *,
                    prefix_col: Optional[Callable]=None,
                    prefix_col_title: Optional[str]=None,
                    show_player: bool=False,
                    show_number: int=0,
                    show_ranks: bool=False,
                    winning_games: bool=False,
                    skip_header: bool=False,
                    datatables: bool=False) -> str:
    """Jinja filter to convert a list of games into a standard table.

    Parameters:
        env: Environment -- passed in automatically
        prefix_col (func): Function to return prefix column's value. Passed each game.
        prefix_col_title (str): Title for the prefix_col column
        show_player (bool): Show the player name column
        show_number (int): If greater than zero, the initial number of rows to display
        show_ranks (bool): Show position ranks
        winning_games (bool): The table has only winning games, so don't show
                              place or end columns, and do show runes.
        skip_header (bool): Skip the header?

    Returns: (string) '<table>contents</table>'.
    """

    def format_trow(game: orm.Game, index: int,
                    hidden_game: bool=False) -> str:
        """Convert a game to a table row."""
        classes = ''
        if game.won and not winning_games:
            classes += "winning-row "
        if hidden_game:
            classes += "hidden-game "

        return trow.format(
            rank='' if not show_ranks else
            """<td class="text-xs-right">%d</td>""" % (index + 1),
            tr_class=classes,
            prefix_col=''
            if not prefix_col else "<td>%s</td>" % prefix_col(game),
            player_row='' if not show_player else "<td>%s</td>" %
            link_player(game.player.url_name, env.globals['urlbase']),
            score='<td class="text-xs-right">{}</td>'.format(
                prettyint(game.score)) if winning_games else '',
            character=game.char,
            full_character=game.species.name + ' ' + game.background.name,
            god=game.god.name,
            place=""
            if winning_games else "<td>%s</td>" % game.place.as_string,
            end="" if winning_games else "<td>%s</td>" % game.pretty_tmsg,
            runes='<td class="text-xs-right">{}</td>'.format(game.runes)
            if winning_games else '',
            turns=prettyint(game.turn),
            duration=prettydur(game.dur),
            date=prettydate(game.end),
            version=game.version.v,
            morgue=morgue_link(game))

    t = """<table id="{id}" class="{classes}">
          <thead>
            <tr>
            {thead}
            </tr>
          </thead>
          <tbody>
            {tbody}
          </tbody>
        </table>"""

    if datatables:
        t += r"""<script>
                $(document).ready(function(){{
                    $('#{id}').DataTable({{
                        "columnDefs": [
                            {{ "searchable": false, "targets": [0,1,5,6,7,9] }},
                            {{ "orderable": false, "targets": [7,9] }}
                        ],
                        "order": [[0, "asc"]],
                        "info": false,
                        "lengthChange": false,
                        "oLanguage": {{
                            "sSearch": "Filter:"
                        }},
                        "pagingType": "numbers"
                    }});

                    $('#{id}_wrapper input[type=search]')
                        .off('cut input keypress keyup paste search')
                        .on( 'keyup change', function () {{
                        var tokens = this.value.trim().split(/\s+/);
                        // Modify tokens to be \bXXXX, if two letters also let match \b..XX\b
                        // This is to only match words from the start, with the exception
                        // of two letter class abbreviations, which match the second
                        // two letters of the combo abbreviation (e.g. match "Be" to "MiBe")
                        tokens = tokens.map(function(t) {{
                            t = "\\\\b" + t + (t.length==2 ? "|\\\\b.."+t+"\\\\b" : "");
                            return t;
                        }});
                        // AND tokens together
                        var regex = "(?=" + tokens.join(")(?=") + ")";
                        table = $('#{id}').DataTable();
                        table.search(regex, true, false);
                        table.draw();
                    }});
                }});
                </script>"""

    thead = """{rank}
              {prefix}
              {player}
              {score}
              <th>Combo</th>
              <th>God</th>
              {place}
              {end}
              {runes}
              <th class="text-xs-right">Turns</th>
              <th class="text-xs-right">Duration</th>
              <th class="text-xs-right">Date</th>
              <th>Version</th>
              <th class="text-xs-center">💀</th>""".format(
        rank='' if not show_ranks else '<th class="text-xs-right"></th>',
        prefix='' if not prefix_col else '<th>%s</th>' % prefix_col_title,
        player='' if not show_player else '<th>Player</th>',
        score='<th class="text-xs-right">Score</th>' if winning_games else '',
        place='' if winning_games else '<th>Place</th>',
        end='' if winning_games else '<th>End</th>',
        runes='<th class="text-xs-right">Runes</th>' if winning_games else '')

    trow = """<tr class="{tr_class}">
      {rank}
      {prefix_col}
      {player_row}
      {score}
      <td><abbr data-toggle="tooltip" title="{full_character}">{character}</abbr></td>
      <td>{god}</td>
      {place}
      {end}
      {runes}
      <td class="text-xs-right">{turns}</td>
      <td class="text-xs-right">{duration}</td>
      <td class="text-xs-right">{date}</td>
      <td>{version}</td>
      <td>{morgue}</td>
    </tr>"""

    tbody = "\n".join(
        format_trow(
            game=game,
            index=index,
            hidden_game=(index >= show_number if show_number > 0 else False))
        for index, game in enumerate(games))

    return t.format(
        id=uuid.uuid4(),
        classes=const.TABLE_CLASSES,
        thead=thead if not skip_header else '',
        tbody=tbody)


def streakstotable(streaks: Sequence[orm.Streak],
                   show_player: bool=True,
                   show_loss: bool=True,
                   limit: Optional[int]=None) -> str:
    """Jinja filter to convert a list of streaks into a standard table.

    Parameters:
        streaks: list of streaks
        show_player (bool): Show the player name column.
        show_loss (bool): Show the losing game column.
        limit (int): The table won't display more games than this.

    Returns: (string) '<table>contents</table>'.
    """

    def format_trow(streak: orm.Streak, show_player: bool,
                    show_loss: bool) -> str:
        """Convert a streak to a table row."""
        player = ""
        loss = ""
        if show_player:
            player = "<td><a href='players/{player_url}.html'>{player_name}<a></td>".format(
                player_url=streak.player.url_name,
                player_name=streak.player.name)
        if show_loss:
            loss = "<td>%s</td>" % 'TODO'

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
               {loss}""".format(
        player='' if not show_player else '<th>Player</th>',
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

    return t.format(
        classes=const.TABLE_CLASSES,
        thead=thead,
        tbody="\n".join(
            format_trow(streak, show_player, show_loss) for streak in streaks))


def mosthighscorestotable(highscores: Iterable) -> str:
    """Jinja filter to convert a list of combo highscores by players into a standard table."""
    table = """<table class="{classes}">
          <thead>
            <tr>
              <th class="text-xs-right"></th>
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

    rank = 0
    for entry in highscores:
        rank += 1
        player = entry[0]
        games = entry[1]
        combos = ', '.join([morgue_link(game, game.char) for game in games])
        tbody += ("""<tr>
                       <td class="text-xs-right">%d</td>
                       <td>%s</td>
                       <td class="text-xs-right">%s</td>
                       <td>%s</td>
                     </tr>""" %
                  (rank, "<a href='players/{player}.html'>{player}<a>".format(
                      player=player), len(games), combos))

    return table.format(classes=const.TABLE_CLASSES, tbody=tbody)


def recordsformatted(records: dict) -> str:
    """Show any records a player holds."""
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
            len(records['race']), ', '.join(
                [morgue_link(game, game.rc) for game in records['race']]))

    if records['role']:
        role = "<p><strong>Backgrounds (%s):</strong> %s</p>" % (
            len(records['role']), ', '.join(
                [morgue_link(game, game.bg) for game in records['role']]))

    if records['god']:
        god = "<p><strong>Gods (%s):</strong> %s</p>" % (
            len(records['god']), ', '.join(
                [morgue_link(game, game.god) for game in records['god']]))

    if records['combo']:
        combo = "<p><strong>Combos (%s):</strong> %s</p>" % (
            len(records['combo']), ', '.join(
                [morgue_link(game, game.char) for game in records['combo']]))

    return result.format(race=race, role=role, god=god, combo=combo)


def morgue_link(game: orm.Game, text: str="Morgue") -> str:
    """Returns a hyperlink to a morgue file.

    Game can be either a gid string or a game object.
    """
    return '<a href="{url}">{text}</a>'.format(
        url=modelutils.morgue_url(game), text=text)


def percentage(n: int, digits: int=2) -> str:
    """Convert a number from 0-1 to a percentage."""
    return "%s" % round(n * 100, digits)


def shortest_win(games: Iterable[orm.Game]) -> orm.Game:
    """Given a list of games, return the win which is the shortest (turns)."""
    wins = filter(lambda g: g.won, games)
    return min(wins, key=lambda g: g.turn)


def fastest_win(games: Iterable[orm.Game]) -> orm.Game:
    """Given a list of games, return the win which is the fastest (time)."""
    wins = filter(lambda g: g.won, games)
    return min(wins, key=lambda g: g.dur)


def highscore(games: orm.Game) -> orm.Game:
    """Given a list of games, return the highest scoring game."""
    return max(games, key=lambda g: g.score)


@jinja2.environmentfilter
def generic_games_to_table(env: jinja2.environment.Environment,
                           data: Iterable) -> str:
    """Convert list of games into a HTML table."""
    return _games_to_table(env, data, show_player=False, winning_games=False)


@jinja2.environmentfilter
def generic_highscores_to_table(env: jinja2.environment.Environment,
                                data: Iterable,
                                show_player: bool=True,
                                show_number: int=0,
                                show_ranks: bool=True,
                                datatables: bool=False) -> str:
    """Convert list of winning games into a HTML table."""
    return _games_to_table(
        env,
        data,
        show_player=show_player,
        show_number=show_number,
        show_ranks=show_ranks,
        winning_games=True,
        datatables=datatables)


@jinja2.environmentfilter
def species_highscores_to_table(env: jinja2.environment.Environment,
                                data: Iterable) -> str:
    """Convert list of games for each species into a HTML table."""
    return _games_to_table(
        env,
        data,
        show_player=True,
        prefix_col=lambda g: g.species.name,
        prefix_col_title='Species',
        winning_games=True)


@jinja2.environmentfilter
def background_highscores_to_table(env: jinja2.environment.Environment,
                                   data: Iterable) -> str:
    """Convert list of games for each background into a HTML table."""
    return _games_to_table(
        env,
        data,
        show_player=True,
        prefix_col=lambda g: g.background.name,
        prefix_col_title='Background',
        winning_games=True)
