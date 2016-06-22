"""Take game data and figure out scoring."""

import time
import datetime

import dateutil.parser

import scoreboard.model as model
import scoreboard.orm as orm
import scoreboard.constants as const


def get_game(gid):
    """Get a game from the database."""
    return model.game(gid)


def is_valid_streak_addition(game, streak):
    """Check if the game is a valid addition to the streak."""
    # Valid if no streak to begin with
    if not streak:
        return True
    # Valid if the game started after the start of the streak
    if isinstance(streak['start'], datetime.datetime):
        start = streak['start']
    else:
        start = dateutil.parser.parse(streak['start'])
    return game.start > start


def is_grief(game):
    """Check if the game is a streak-breaking grief.

    This involves experimental anti-griefing heuristics.
    """
    name = game['name']

    # Not a grief if not the player's first game on a server
    src = game['src']
    first_game = model.first_game(name, src)
    if game['gid'] != first_game['gid']:
        return False

    # Were consumables used?
    if ('potionsused' in game.raw_data and (game.raw_data['potionsused'] > 0 or
                                            game.raw_data['scrollsused'] > 0)):
        # Tighter thresholds for grief detection
        if game['dur'] < 600 or game['turn'] < 1000:
            blacklist_player(name, src)
            return True
    else:
        # Very loose thresholds for grief detection
        if game['dur'] < 1200 or game['turn'] < 5000:
            blacklist_player(name, src)
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


def score_game_vs_streaks(game):
    """Extend active streaks if a game was won and finalise streak stats."""

    # Retrieve active streaks
    active_streaks = model.get_active_streaks(s, player=game.player)
    streak = active_streaks.get(cname)

    # Ignore game if not a valid streak addition
    if not is_valid_streak_addition(game, streak):
        return

    if game.ktyp == 'winning':
        # Extend or start a streak
        if streak:
            streak['wins'].append(game.gid)
            streak['end'] = game.end
        else:
            streak = {'cname': game.player.name.lower(),
                      'wins': [game.gid],
                      'start': game.end}
        # Update the active streak dict
        active_streaks[cname] = streak
    else:
        # Finalise 2+ win streaks
        if streak and len(streak['wins']) > 1:

            # Ignore game if griefing detected
            if is_grief(game):
                return

            completed_streaks = load_global_stat('completed_streaks', [])
            streak['streak_breaker'] = game.games_gid
            completed_streaks.append(streak)
            set_global_stat('completed_streaks', completed_streaks)

        if cname in active_streaks:
            del active_streaks[cname]
        else:
            # No need to adjust active_streaks
            return
    # Update global stat with new active streak dict
    set_global_stat('active_streaks', active_streaks)


def score_game(game):
    """Score a single game."""
    # Increment wins
    if game.ktyp == 'winning':
        pass
        # Check greatplayer
        # Check greaterplayer
        # Check for great race completion
        # Check for great role completion

        # Check streaks
        score_game_vs_streaks(game)

        # Finalise the changes to stats
    game.scored = True
    return game


def game_is_blacklisted(game, blacklist):
    for entry in blacklist:
        if game.player.id == entry.id:
            return True
    return False


def score_games(rebuild=False):
    """Update stats with all unscored game.

    If rebuild == True, rebuilds the database as well.
    """
    print("Scoring all games...")
    start = time.time()
    scored = 0

    scored_players = set()

    s = orm.get_session()

    # Load blacklisted players into cache
    blacklisted_players = model.list_accounts(s, blacklisted=True)

    if rebuild:
        rebuild_database()

    while True:
        games = model.list_games(s, scored=False, limit=5000)
        if not games:
            break
        for game in games:
            if game_is_blacklisted(game, blacklisted_players):
                continue
            game = score_game(game)
            s.add(game)
            scored_players.add(game.account.player.name)
            scored += 1
            if scored % 10000 == 0 and scored > 0:
                print(scored)
        s.commit()

    # Add manual achievements
    add_manual_achievements(s)

    end = time.time()
    print("Scored %s new games (for %s players) in %s secs" %
          (scored, len(scored_players), round(end - start, 2)))

    return scored_players


if __name__ == "__main__":
    score_games()
