"""Take game data and figure out scoring."""

import time
import datetime

import scoreboard.model as model
import scoreboard.orm as orm
import scoreboard.constants as const


def get_game(gid):
    """Get a game from the database."""
    raise NotImplementedError("deprecated method")


def is_valid_streak_addition(game, current_streak):
    """Check if the game is a valid addition to the streak."""
    # Valid if no streak to begin with
    if not current_streak:
        return True
    # TODO Valid if the game started after the start of the streak
    return True


def is_grief(s, game):
    """Check if the game is a streak-breaking grief.

    This involves experimental anti-griefing heuristics.
    """

    # Only an account's first game can be auto-detected as a grief
    first_game = model.list_games(s, account=game.account, reverse_order=True,
                                  limit=1)
    if first_game != game:
        return False

    # Were consumables used?
    if game.potions_used > 0 or games.scrolls_used > 0:
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


def blacklist_player(name, src):
    """Add a player-server combo to the blacklist."""
    add_to_blacklist_cache(name, src)
    model.add_player_to_blacklist(name, src)


def is_blacklisted(name, src):
    """Check if the player is in a blacklist."""
    if name in const.BLACKLISTS['bots']:
        return True
    if src in const.BLACKLISTS['griefers'].get(name, {}):
        return True
    if src in BLACKLISTED_PLAYERS_CACHE.get(name, []):
        return True
    return False


def add_to_blacklist_cache(name, src):
    """Add player to the blacklisted players cache."""
    if name not in BLACKLISTED_PLAYERS_CACHE:
        BLACKLISTED_PLAYERS_CACHE[name] = [src]
    else:
        BLACKLISTED_PLAYERS_CACHE[name] += src


def load_global_stat(key, default=None):
    """Load a global stat key from db/cache.

    If the key doesn't exist, return default.
    """
    if key in GLOBAL_STATS_CACHE:
        val = GLOBAL_STATS_CACHE[key]
    else:
        val = model.global_stat(key)
    if val is None:
        return default
    else:
        return val


def set_global_stat(key, data):
    """Save a global stat key to cache.

    The cache is cleared out at the end of score_games.
    """
    GLOBAL_STATS_CACHE[key] = data


def rescore_player(player):
    """Rescore all of player's games and stats."""
    try:
        model.delete_player_streaks(player)
        model.delete_player_stats(player)
        model.unscore_all_games_of_player(player)
    except model.DatabaseError as e:
        print(e)


def rebuild_database():
    """Rebuild the database by unscoring all games and deleting stats."""
    model.unscore_all_games()
    model.delete_all_player_stats()
    model.delete_all_global_stats()


def add_manual_achievements(s):
    """Add manual achievements to players' stats."""
    for name, achievements in const.MANUAL_ACHIEVEMENTS.items():
        player = model.get_player(s, name)
        for achievement, value in achievements.items():
            cheevo = model.get_achievement(s, achievement)
            if cheevo and cheevo not in player.achievements:
                player.achievements.append(cheevo)
                s.add(player)
            elif not cheevo:
                print("Warning: couldn't find manually specified achievement"
                      " %s in the database!" % achievement)
    s.commit()


def great_race(race, player_stats, achievements):
    """Check if the player has achieved great race for the given race.

    Returns True or False.

    Note: Requires player_stats['race_wins'] to already have been updated with
    this games's result.
    """
    # Check the race has a greatrace achievement
    if race not in const.RACE_TO_GREAT_RACE:
        return False
    achievement = const.RACE_TO_GREAT_RACE[race]
    # Might have already achieved it
    if achievement in achievements:
        return True
    # Check we actually have enough potential wins (for speed)
    if player_stats['race_wins'][race] < len(const.PLAYABLE_ROLES):
        return False
    # Check for completion
    roles_won = set(get_game(gid)['char'][2:] for gid in player_stats['wins']
                    if race == get_game(gid).rc)
    if not const.PLAYABLE_ROLES - roles_won:
        achievements[achievement] = True
        return True
    return False


def great_role(role, player_stats, achievements):
    """Check if the player has achieved great role for the given role.

    Returns True or False.

    Note: Requires player_stats['role_wins'] to already have been updated with
    this games's result.
    """
    # Check the role has a greatrole achievement
    if role not in const.ROLE_TO_GREAT_ROLE:
        return False
    achievement = const.ROLE_TO_GREAT_ROLE[role]
    # Might have already achieved it
    if achievement in achievements:
        return True
    # Check we actually have enough potential wins (for speed)
    if player_stats['role_wins'][role] < len(const.PLAYABLE_RACES):
        return False
    # Check for completion
    races_won = set(get_game(gid)['char'][:2] for gid in player_stats['wins']
                    if role == get_game(gid)['char'][2:])
    if not const.PLAYABLE_RACES - races_won:
        achievements[achievement] = True
        return True
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

    else: # Game wasn't won
        # If there was no active streak, we're done
        if not current_streak:
            return
        # Ignore game if griefing detected
        if is_grief(s, game):
            return
        # Close any active streak
        current_streak.active = False
        s.add(current_streak)


def score_game(s, game: orm.Game):
    """Score a single game.

    Parameters:
        s: db session
        game: game to score.

    Returns: Nothing
    """
    handle_player_streak(s, game)
    # Increment wins
    if game.ktyp == 'winning':
        pass
        # Check greatplayer
        # Check greaterplayer
        # Check for great race completion
        # Check for great role completion

        # Finalise the changes to stats


def game_is_blacklisted(game, blacklist):
    for entry in blacklist:
        if game.player.id == entry.id:
            return True
    return False


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
            if game.account.blacklisted:
                continue
            score_game(s, game)
            game.scored = True
            s.add(game)
            scored_players.add(game.player)
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