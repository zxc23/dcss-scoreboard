"""Take game data and figure out scoring."""

import time

import scoreboard.model as model
import scoreboard.orm as orm
import scoreboard.constants as const


def is_valid_streak_addition(
        game, current_streak):  # pylint: disable=unused-argument
    """Check if the game is a valid addition to the streak."""
    # Valid if no streak to begin with
    if not current_streak:
        return True
    # TODO Validate if the game started after the start of the streak
    return True


def is_grief(s, game):
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


def add_manual_achievements(s):
    """Add manual achievements to players' stats."""
    for name, achievements in const.MANUAL_ACHIEVEMENTS.items():
        player = model.get_player(s, name)
        for achievement in achievements.keys():
            cheevo = model.get_achievement(s, achievement)
            if cheevo and cheevo not in player.achievements:
                player.achievements.append(cheevo)
                s.add(player)
            elif not cheevo:
                print("Warning: couldn't find manually specified achievement"
                      " %s in the database!" % achievement)
    s.commit()


def great_race(player, species):  # pylint: disable=unused-argument
    """Check if the player has great race.

    Returns True or False.
    """
    # Check we haven't already achieved this
    # Check we actually have enough potential wins for greatrace (for speed)
    # Check for completion
    return False


def great_role(player, background):  # pylint: disable=unused-argument
    """Check if a player has great role.

    Returns True or False.
    """
    # Check we haven't already achieved this
    # Check we actually have enough potential wins for greatrole (for speed)
    # Check for completion
    return False


def handle_player_streak(s, game: orm.Game):
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


def score_game(s, game: orm.Game):
    """Score a single game.

    Parameters:
        s: db session
        game: game to score.

    Returns: Nothing
    """
    if game.account.blacklisted:
        return
    handle_player_streak(s, game)
    # Increment wins
    if game.ktyp == 'winning':
        pass
        # Check greatplayer
        # Check greaterplayer
        # Check for great race completion
        # Check for great role completion

        # Finalise the changes to stats


def score_games():
    """Score all unscored games."""
    print("Scoring all games...")
    start = time.time()
    scored = 0

    scored_players = set()

    s = orm.get_session()

    while True:
        games = model.list_games(s, scored=False, limit=100)
        if not games:
            break
        for game in games:
            score_game(s, game)
            game.scored = True
            s.add(game)
            scored_players.add(game.player.name)
            scored += 1
            if scored and scored % 10000 == 0:
                print(scored)
        s.commit()

    # Add manual achievements
    add_manual_achievements(s)

    end = time.time()
    print("Scored %s new games (for %s players) in %s secs" %
          (scored, len(scored_players), round(end - start, 2)))

    return scored_players
