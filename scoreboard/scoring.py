"""Take game data and figure out scoring."""

import time
from typing import Sequence

import sqlalchemy.orm  # for sqlalchemy.orm.session.Session type hints

import scoreboard.model as model
import scoreboard.orm as orm
import scoreboard.constants as const


def is_valid_streak_addition(
        game: orm.Game, current_streak:
        orm.Streak) -> bool:  # pylint: disable=unused-argument
    """Check if the game is a valid addition to the streak."""
    # Valid if no streak to begin with
    if not current_streak:
        return True
    # TODO Validate if the game started after the start of the streak
    return True


def is_grief(s: sqlalchemy.orm.session.Session, game: orm.Game) -> bool:
    """Check if the game is a streak-breaking grief.

    This involves experimental anti-griefing heuristics.
    """

    # Only an account's first game can be auto-detected as a grief
    first_game = model.list_games(
        s, account=game.account, reverse_order=True, limit=1)
    if first_game != game:
        return False

    # Were consumables used?
    if game.potions_used > 0 or game.scrolls_used > 0:
        # Tighter thresholds for grief detection
        if game.dur < 600 or game.turn < 1000:
            # TODO: blacklist_account(game.account)
            return True
    else:
        # Very loose thresholds for grief detection
        if game.dur < 1200 or game.turn < 5000:
            # TODO: blacklist_account(game.account)
            return True
    return False


def handle_player_streak(s: sqlalchemy.orm.session.Session, game:
                         orm.Game) -> None:
    """Figure out what a game means for the player's streak.

    A first win will start a streak.
    A subsequent win (if it started after the last win) will extend the streak.
    A loss will end any active streak.
    """
    current_streak = model.get_player_streak(s, game.player)

    if game.won:
        # Start or extend a streak
        if not current_streak:
            current_streak = model.create_streak(s, game.player)
        else:
            # Ignore game if not a valid streak addition
            if not is_valid_streak_addition(game, current_streak):
                return
        game.streak = current_streak

    else:  # Game wasn't won
        # If there is no active streak, we're done
        if not current_streak:
            return
        # Ignore game if griefing detected
        if is_grief(s, game):
            return
        # If the game is a non-grief loss, close the active streak
        current_streak.active = False
        s.add(current_streak)


def _add_achievement(s: sqlalchemy.orm.session.Session, player: orm.Player,
                     key: str) -> None:
    achievement = model.get_achievement(s, key)
    if achievement not in player.achievements:
        # print("Adding %s to %s" % (key, player.name))
        player.achievements.append(achievement)
        s.add(player)

# def handle_greatfoo_achievements(s, game):
# pass


def handle_achievements(s: sqlalchemy.orm.session.Session, game:
                        orm.Game) -> None:
    """Figure out if a game should award a player achievements."""
    if game.won:
        _add_achievement(s, game.player, 'won1')
        if game.dur < 9000:
            _add_achievement(s, game.player, 'wondur2.5hr')
        if game.turn < 55555:
            _add_achievement(s, game.player, 'fivebyfive')
        # handle_greatfoo_achievements(s, game)
    else:
        if any(map(game.tmsg.startswith, const.GHOST_KILL_VERBS)):
            _add_achievement(s, game.player, 'gselfkill')
        if game.runes > 2:
            _add_achievement(s, game.player, 'lostwith3+runes')
        if game.tdam > 74:
            _add_achievement(s, game.player, '75tdam')


def score_game(s: sqlalchemy.orm.session.Session, game: orm.Game) -> None:
    """Score a single game.

    Parameters:
        s: db session
        game: game to score.

    Returns: Nothing
    """
    if game.account.blacklisted:
        return
    handle_player_streak(s, game)
    handle_achievements(s, game)


def score_games() -> set:
    """Score all unscored games."""
    start = time.time()
    scored_players = set()
    s = orm.get_session()
    new_scored = 0
    print("Scoring games...")
    while True:
        games = model.list_games(s, scored=False, limit=100)
        if not games:
            break
        for game in games:
            score_game(s, game)
            game.scored = True
            s.add(game)
            scored_players.add(game.player.name)
            new_scored += 1
            if new_scored and new_scored % 10000 == 0:
                print(new_scored)
        s.commit()

    end = time.time()
    print("Scored %s new games (for %s players) in %s secs" %
          (new_scored, len(scored_players), round(end - start, 2)))

    return scored_players
