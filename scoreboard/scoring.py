"""Take game data and figure out scoring."""

import time
import datetime

import pylru
import dateutil.parser

from . import model
from . import constants as const

PLAYER_STATS_CACHE = pylru.lrucache(1000, callback=model.set_player_stats)
GLOBAL_STATS_CACHE = pylru.lrucache(1000, callback=model.set_global_stat)
BLACKLISTED_PLAYERS_CACHE = pylru.lrucache(1000)


def get_game(gid):
    """Get a game from the database."""
    return model.game(gid)


def is_valid_streak_addition(game, streak):
    """Check if the game is a valid addition to the streak."""
    # Extend active streak only if win started after previous game end
    if isinstance(streak['start'], datetime.datetime):
        end = streak['start']
    else:
        end = dateutil.parser.parse(streak['start'])
    if len(streak['wins']) == 0:
        return True
    return game.start > end


def is_grief(game):
    """Check if the game is a streak-breaking grief.

    This involves experimental anti-griefing heuristics.
    """
    # First time playing a server and fast loss
    name = game['name']
    src = game['src']
    first_game = model.first_game(name, src)
    if game['gid'] == first_game['gid'] and (game['dur'] < 1200 or
                                             game['turn'] < 1000):
        model.add_player_to_blacklist(name, src)
        add_to_blacklist_cache(name, src)
        return True
    return False


def is_blacklisted(name, src):
    """Check if the player is in a blacklist."""
    if name in const.BLACKLISTS['bots']:
        return True
    if src in const.BLACKLISTS['griefers'].get(name, {}):
        return True
    if src in BLACKLISTED_PLAYERS_CACHE.get(name, []):
        return True
    return False


def load_blacklisted_players():
    """Load blacklisted players into a read cache."""
    for name, src in model.all_blacklisted_players():
        add_to_blacklist_cache(name, src)


def add_to_blacklist_cache(name, src):
    """Add player to the blacklisted players cache."""
    if name not in BLACKLISTED_PLAYERS_CACHE:
        BLACKLISTED_PLAYERS_CACHE[name] = [src]
    else:
        BLACKLISTED_PLAYERS_CACHE[name] += src


def load_player_stats(name):
    """Load the stats dictionary of a player."""
    # Try to load stats from cache
    if name in PLAYER_STATS_CACHE:
        stats = PLAYER_STATS_CACHE[name]
    else:
        stats = model.get_player_stats(name)

    if not stats:
        # Create initial stats
        stats = {'wins': [],
                 'games': 0,
                 'winrate': 0,
                 'total_playtime': 0,
                 'total_score': 0,
                 'avg_score': 0,
                 'boring_games': 0,
                 'boring_rate': 0,
                 'god_wins': {k: 0
                              for k in const.PLAYABLE_GODS},
                 'race_wins': {k: 0
                               for k in const.PLAYABLE_RACES},
                 'role_wins': {k: 0
                               for k in const.PLAYABLE_ROLES},
                 'achievements': {},
                 'last_active': None}
    return stats


def set_player_stats(name, stats):
    """Save player stats to the LRU cache.

    Note: The cache should be cleared out at the end of score_games.
    """
    PLAYER_STATS_CACHE[name] = stats


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


def add_manual_achievements():
    """Add manual achievements to players' stats."""
    for player in const.MANUAL_ACHIEVEMENTS:
        stats = load_player_stats(player)
        if stats['games'] == 0:
            continue
        for achievement, value in const.MANUAL_ACHIEVEMENTS[player].items():
            stats['achievements'][achievement] = value
        set_player_stats(player, stats)


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
    roles_won = set(get_game(gid)['char'][2:]
                    for gid in player_stats['wins']
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
    races_won = set(get_game(gid)['char'][:2]
                    for gid in player_stats['wins']
                    if role == get_game(gid)['char'][2:])
    if not const.PLAYABLE_RACES - races_won:
        achievements[achievement] = True
        return True
    return False


def score_game_vs_streaks(game, won):
    """Extend active streaks if a game was won and finalise streak stats."""
    active_streaks = load_global_stat('active_streaks', {})
    name = game.name
    if won:
        # Extend or start a streak
        if name in active_streaks:
            if is_valid_streak_addition(game, active_streaks[name]):
                active_streaks[name]['wins'].append(game.gid)
                active_streaks[name]['end'] = game.end
        else:
            active_streaks[name] = {'player': name,
                                    'wins': [game.gid],
                                    'start': game.start,
                                    'end': game.end}
    else:
        # If the player was on a 2+ game streak, finalise it
        streak = active_streaks.get(name)
        if streak and len(streak['wins']) > 1:
            # Ignore game if griefing detected
            if is_grief(game):
                return
            completed_streaks = load_global_stat('completed_streaks', [])
            streak['streak_breaker'] = game.gid
            streak['end'] = game.end
            completed_streaks.append(streak)
            set_global_stat('completed_streaks', completed_streaks)
        if name in active_streaks:
            del active_streaks[name]
        else:
            # No need to adjust active_streaks
            return
    set_global_stat('active_streaks', active_streaks)


def score_game(game_row):
    """Score a single game."""
    gid = game_row.gid
    game = game_row.raw_data
    name = game_row.name
    src = game_row.src

    # Skip if player blacklisted
    if is_blacklisted(name, src):
        model.mark_game_scored(gid)
        return

    # Log vars
    god = game['god']
    score = game['sc']
    race = game['rc']
    role = game['bg']
    won = game['ktyp'] == 'winning'

    # Player vars
    stats = load_player_stats(name)
    achievements = stats['achievements']
    wins = len(stats['wins'])

    # Start updating stats
    stats['games'] += 1
    stats['last_active'] = game['end']
    stats['total_playtime'] += game['dur']

    # Increment wins
    if won:
        stats['wins'].append(game_row.gid)
        wins += 1

        # Adjust fastest_realtime win
        if 'fastest_realtime' not in stats or game['dur'] < stats[
                'fastest_realtime']['dur']:
            stats['fastest_realtime'] = game

        # Adjust fastest_turncount win
        if 'fastest_turncount' not in stats or game['turn'] < stats[
                'fastest_turncount']['turn']:
            stats['fastest_turncount'] = game

        # Increment god_wins and check polytheist
        if god in stats['god_wins']:
            stats['god_wins'][god] += 1
            if stats['god_wins'][god] == 1 and not const.PLAYABLE_GODS - {
                    g
                    for g, w in stats['god_wins'].items() if w > 0
            }:
                achievements['polytheist'] = True
        else:
            stats['god_wins'][god] += 1

        # Increment race_wins and check greatplayer
        if race in stats['race_wins'] and stats['race_wins'][race] > 0:
            stats['race_wins'][race] += 1
        else:
            stats['race_wins'][race] = 1
            if not const.PLAYABLE_RACES - set(
                [race
                 for race in stats['race_wins'].keys()
                 if stats['race_wins'][race] > 0]):
                achievements['greatplayer'] = True

        # Increment role_wins and check greaterplayer
        if role in stats['role_wins'] and stats['role_wins'][role] > 0:
            stats['role_wins'][role] += 1
        else:
            stats['role_wins'][role] = 1

        if 'greatplayer' in achievements and not const.PLAYABLE_ROLES - set(
            [role
             for role in stats['role_wins'].keys()
             if stats['role_wins'][role] > 0]):
            achievements['greaterplayer'] = True

        # Adjust avg_win stats
        # Older logfiles didn't have these fields, so skip those games
        if 'ac' in game:
            if 'avg_win_ac' not in stats:
                stats['avg_win_ac'] = game['ac']
            else:
                stats['avg_win_ac'] += (
                    game['ac'] - stats['avg_win_ac']) / wins
            if 'avg_win_ev' not in stats:
                stats['avg_win_ev'] = game['ev']
            else:
                stats['avg_win_ev'] += (
                    game['ev'] - stats['avg_win_ev']) / wins
            if 'avg_win_sh' not in stats:
                stats['avg_win_sh'] = game['sh']
            else:
                stats['avg_win_sh'] += (
                    game['sh'] - stats['avg_win_sh']) / wins

        # Adjust win-based achievements
        if wins >= 10:
            achievements['goodplayer'] = True
        if wins >= 100:
            achievements['centuryplayer'] = True

        # Check for great race completion
        if great_race(race, stats, achievements):
            achievements[const.RACE_TO_GREAT_RACE[race]] = True

        # Check for great role completion
        if great_role(role, stats, achievements):
            achievements[const.ROLE_TO_GREAT_ROLE[role]] = True

        # Older logfiles don't have these fields, so skip those games
        if 'potionsused' in game and game['potionsused'] == 0 and game[
                'scrollsused'] == 0:
            if 'no_potion_or_scroll_win' not in achievements:
                achievements['no_potion_or_scroll_win'] = 1
            else:
                achievements['no_potion_or_scroll_win'] += 1

        if 'zigdeepest' in game and game['zigdeepest'] == '27':
            if 'cleared_zig' not in achievements:
                achievements['cleared_zig'] = 1
            else:
                achievements['cleared_zig'] += 1

    else:  # !won
        # Increment boring_games
        if game['ktyp'] in ('leaving', 'quitting'):
            stats['boring_games'] += 1

    # Update other player stats
    if 'highscore' not in stats or score > stats['highscore']['sc']:
        stats['highscore'] = game
    stats['winrate'] = wins / stats['games']
    stats['total_score'] += score
    stats['avg_score'] = stats['total_score'] / stats['games']
    stats['boring_rate'] = stats['boring_games'] / stats['games']

    # Check streaks
    score_game_vs_streaks(game_row, won)

    # Finalise the changes to stats
    set_player_stats(name, stats)
    model.mark_game_scored(gid)


def score_games(rebuild=False):
    """Update stats with all unscored game.

    If rebuild == True, rebuilds the database as well.
    """
    print("Scoring all games...")
    start = time.time()
    scored = 0

    scored_players = set()

    # Load blacklisted players into cache
    load_blacklisted_players()

    if rebuild:
        rebuild_database()

    while True:
        games = model.all_games(scored=False, limit=5000)
        if not games:
            break
        for game in games:
            score_game(game)
            scored_players.add(game.name)
            scored += 1
            if scored % 10000 == 0 and scored > 0:
                print(scored)

    # Add manual achievements
    add_manual_achievements()

    # Now we have to write out everything remaining in the cache
    for name, stats in PLAYER_STATS_CACHE.items():
        model.set_player_stats(name, stats)
    for key, data in GLOBAL_STATS_CACHE.items():
        model.set_global_stat(key, data)
    end = time.time()
    print("Scored %s new games (for %s players) in %s secs" %
          (scored, len(scored_players), round(end - start, 2)))

    return scored_players


if __name__ == "__main__":
    score_games()
