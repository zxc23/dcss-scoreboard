"""Take game data and figure out scoring."""

import time
import multiprocessing
from collections import deque

import pylru

from . import model, constants

PLAYER_STATS_CACHE = pylru.lrucache(1000, callback=model.set_player_stats)
GLOBAL_STATS_CACHE = pylru.lrucache(1000, callback=model.set_global_stat)


def clean_up_active_streaks(streaks):
    """Remove single game "streaks"."""
    return {k: v for k, v in streaks.items() if len(v) > 1}


def is_valid_streak_addition(game, streak):
    """Check if the game is a valid addition to the streak."""
    # Extend active streak only if win started after previous game end
    if len(streak) == 0:
        return True
    return game['start'][:-1] > streak[-1]['end']


def load_player_stats(name):
    """Load the stats dictionary of a player.

    This requires applying some transformations to the raw stored data.
    """
    if name in PLAYER_STATS_CACHE:
        stats = PLAYER_STATS_CACHE[name]
    else:
        stats = model.get_player_stats(name)

    if stats:
        stats['last_5_games'] = deque(stats['last_5_games'], 5)
    else:
        stats = {'wins': [],
                 'games': 0,
                 'winrate': 0,
                 'total_score': 0,
                 'avg_score': 0,
                 'last_5_games': deque([], 5),
                 'boring_games': 0,
                 'boring_rate': 0,
                 'god_wins': {k: 0 for k in constants.PLAYABLE_GODS},
                 'race_wins': {k: 0 for k in constants.PLAYABLE_RACES},
                 'role_wins': {k: 0 for k in constants.PLAYABLE_ROLES},
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
        val = model.get_global_stat(key)
    if val is None:
        return default
    else:
        return val


def set_global_stat(key, data):
    """Save a global stat key to cache.

    The cache is cleared out at the end of score_games.
    """
    GLOBAL_STATS_CACHE[key] = data


def great_race(race, player_stats, achievements):
    """Check if the player has achieved great race for the given race.

    Returns True or False.

    Note: Requires player_stats['race_wins'] to already have been updated with this
    games's result.
    """
    # Check the race has a greatrace achievement
    if race not in constants.RACE_TO_GREAT_RACE:
        return False
    achievement = constants.RACE_TO_GREAT_RACE[race]
    # Might have already achieved it
    if achievement in achievements:
        return True
    # Check we actually have enough potential wins (for speed)
    if player_stats['race_wins'][race] < len(constants.PLAYABLE_ROLES):
        return False
    # Check for completion
    roles_won = set(win['char'][2:]
                    for win in player_stats['wins'] if race == win['char'][:2])
    if not constants.PLAYABLE_ROLES - roles_won:
        achievements[achievement] = True
        return True
    return False


def great_role(role, player_stats, achievements):
    """Check if the player has achieved great role for the given role.

    Returns True or False.

    Note: Requires player_stats['role_wins'] to already have been updated with this
    games's result.
    """
    # Check the role has a greatrole achievement
    if role not in constants.ROLE_TO_GREAT_ROLE:
        return False
    achievement = constants.ROLE_TO_GREAT_ROLE[role]
    # Might have already achieved it
    if achievement in achievements:
        return True
    # Check we actually have enough potential wins (for speed)
    if player_stats['role_wins'][role] < len(constants.PLAYABLE_RACES):
        return False
    # Check for completion
    races_won = set(win['char'][:2]
                    for win in player_stats['wins'] if role == win['char'][2:])
    if not constants.PLAYABLE_RACES - races_won:
        achievements[achievement] = True
        return True
    return False


def score_game_vs_global_highscores(game, fields):
    """Update global highscores with log's data.

    Returns True if a global record was updated.
    """
    result = False
    for field in fields:
        fieldval = game[field]
        highscores = load_global_stat(field + '_highscores', {})
        if fieldval not in highscores or game[
                'sc'] > highscores[fieldval]['sc']:
            highscores[fieldval] = game
            set_global_stat(field + '_highscores', highscores)
            result = True
    return result


def score_game_vs_misc_stats(game):
    """Compare a game log with various misc global stats.

    Note: Currently assumes the game was won.
    """
    dur = game['dur']
    turns = game['turn']

    min_dur = load_global_stat('min_dur', [])
    if not min_dur or len(min_dur) < 5:
        min_dur.append(game)
    else:
        if dur < min(i['dur'] for i in min_dur):
            min_dur.append(game)
            min_dur = sorted(min_dur, key=lambda i: i['dur'])[:5]
    set_global_stat('min_dur', min_dur)

    min_turn = load_global_stat('min_turn', [])
    if not min_turn or len(min_turn) < 5:
        min_turn.append(game)
    else:
        if turns < min(i['turn'] for i in min_turn):
            min_turn.append(game)
            min_turn = sorted(min_turn, key=lambda i: i['turn'])[:5]
    set_global_stat('min_turn', min_turn)


def score_game_vs_streaks(game, won):
    """Extend active streaks if a game was won and finalise streak stats."""
    active_streaks = load_global_stat('active_streaks', {})
    name = game['name']
    if won:
        # Extend or start a streak
        if name in active_streaks:
            if is_valid_streak_addition(game, active_streaks[name]):
                active_streaks[name].append(game)
        else:
            active_streaks[name] = [game]
    else:
        # If the player was on a 2+ game streak, record it
        if len(active_streaks.get(name, [])) > 1:
            completed_streaks = load_global_stat('completed_streaks', [])
            streak = active_streaks[name]
            completed_streaks.append({'player': name,
                                      'wins': streak,
                                      'streak_breaker': game,
                                      'start': streak[0]['start'],
                                      'end': streak[-1]['end']})
            set_global_stat('completed_streaks', completed_streaks)
        if name in active_streaks:
            del active_streaks[name]
        else:
            # No need to adjust active_streaks
            return
    set_global_stat('active_streaks', active_streaks)


def score_game(game_row):
    """Score a single game."""
    gid = game_row[0]
    game = game_row[1]

    # Log vars
    name = game['name']
    god = game['god']
    score = game['sc']
    race = game['rc']
    role = game['bg']
    won = game['ktyp'] == 'winning'

    # Player vars
    stats = load_player_stats(name)
    achievements = stats['achievements']
    wins = len(stats['wins'])

    # Increment games
    stats['games'] += 1
    stats['last_active'] = game['end']

    # Increment wins
    if won:
        stats['wins'].append(game)

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
            if stats['god_wins'][god] == 1 and not constants.PLAYABLE_GODS - \
                    {g for g, w in stats['god_wins'].items() if w > 0}:
                achievements['polytheist'] = True
        else:
            stats['god_wins'][god] += 1

        # Increment race_wins and check greatplayer
        if race in stats['race_wins'] and stats['race_wins'][race] > 0:
            stats['race_wins'][race] += 1
        else:
            stats['race_wins'][race] = 1
            if not constants.PLAYABLE_RACES - \
                    set([race for race in stats['race_wins'].keys() if stats['race_wins'][race] > 0]):
                achievements['greatplayer'] = True

        # Increment role_wins and check greaterplayer
        if role in stats['role_wins'] and stats['role_wins'][role] > 0:
            stats['role_wins'][role] += 1
        else:
            stats['role_wins'][role] = 1

        if 'greatplayer' in achievements and not constants.PLAYABLE_ROLES - \
                set([role for role in stats['role_wins'].keys() if stats['role_wins'][role] > 0]):
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
            achievements[constants.RACE_TO_GREAT_RACE[race]] = True

        # Check for great role completion
        if great_role(role, stats, achievements):
            achievements[constants.ROLE_TO_GREAT_ROLE[role]] = True

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

        # Compare win against misc global stats
        score_game_vs_misc_stats(game)

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
    stats['last_5_games'].append(game)
    stats['boring_rate'] = stats['boring_games'] / stats['games']

    # Check global highscore records
    if score_game_vs_global_highscores(game, ['char']):
        # Only check rc and bg records if char record was broken
        score_game_vs_global_highscores(game, ['rc', 'bg'])
    score_game_vs_global_highscores(game, ['god'])

    # Check streaks
    score_game_vs_streaks(game, won)

    # Finalise the changes to stats
    set_player_stats(name, stats)
    model.mark_game_scored(gid)


def score_games():
    """Update scores with all game's data."""
    print("Scoring all games...")
    start = time.time()
    scored = 0

    #p = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    jobs = []
    for game in model.get_all_games(scored=False):
        #jobs.append(p.apply_async(score_game, (game,)))
        score_game(game)

    # for async_job in jobs:
        # async_job.wait()

        # Periodically print our progress
        scored += 1
        if scored % 10000 == 0:
            print(scored)

    # clean up single-game "streaks"
    set_global_stat(
        'active_streaks',
        clean_up_active_streaks(load_global_stat('active_streaks')))

    # Now we have to write out everything remaining in the cache
    for name, stats in PLAYER_STATS_CACHE.items():
        model.set_player_stats(name, stats)
    for key, data in GLOBAL_STATS_CACHE.items():
        model.set_global_stat(key, data)
    end = time.time()
    print("Scored %s games in %s secs" % (scored, round(end - start, 2)))


if __name__ == "__main__":
    score_games()
