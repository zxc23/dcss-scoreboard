"""Take game data and figure out scoring."""

import collections
import time

from . import model

# XXX these should be in the database
PLAYABLE_RACES = {'Ce', 'DD', 'DE', 'Dg', 'Ds', 'Dr', 'Fe', 'Fo', 'Gh', 'Gr',
                  'HE', 'HO', 'Ha', 'Hu', 'Ko', 'Mf', 'Mi', 'Mu', 'Na', 'Op',
                  'Og', 'Sp', 'Te', 'Tr', 'VS', 'Vp'}
PLAYABLE_ROLES = {'AE', 'AK', 'AM', 'Ar', 'As', 'Be', 'CK', 'Cj', 'EE', 'En',
                  'FE', 'Fi', 'Gl', 'Hu', 'IE', 'Mo', 'Ne', 'Sk', 'Su', 'Tm',
                  'VM', 'Wn', 'Wr', 'Wz'}
PLAYABLE_GODS = {'Ashenzari', 'Beogh', 'Cheibriados', 'Dithmenos', 'Elyvilon',
                 'Fedhas', 'Gozag', 'Jiyva', 'Kikubaaqudgha', 'Lugonu',
                 'Makhleb', 'Nemelex Xobeh', 'Okawaru', 'Pakellas', 'Qazlal',
                 'Ru', 'Sif Muna', 'the Shining One', 'Trog', 'Vehumet', 'Xom',
                 'Yredelemnul', 'Zin'}


def load_player_scores(name):
    """Load the score dictionary of a player.

    This requires applying some transformations to the raw stored data.
    """
    data = model.get_player_score_data(name)

    if data:
        data['last_5_games'] = collections.deque(data['last_5_games'], 5)
    else:
        data = {'wins': [],
                'games': 0,
                'winrate': 0,
                'total_score': 0,
                'avg_score': 0,
                'last_5_games': collections.deque([], 5),
                'boring_games': 0,
                'boring_rate': 0,
                'god_wins': {},
                'race_wins': {},
                'role_wins': {},
                'achievements': {}}

    return data


def score_games():
    """Update scores with all game's data."""
    print("Scoring all games...")
    start = time.time()
    scored = 0
    for gid, log in model.games():
        # Periodically print our progress
        scored += 1
        if scored % 10000 == 0:
            print(scored)

        name = log['name']
        scores = load_player_scores(name)

        # Log vars
        if 'god' in log:
            god = log['god']
        else:
            god = 'no_god'
        score = log['sc']
        race = log['char'][:2]
        role = log['char'][2:]

        # Player vars
        achievements = scores['achievements']
        wins = len(scores['wins'])

        # Increment games
        scores['games'] += 1

        # Increment wins
        if log['ktyp'] == 'winning':
            scores['wins'].append(log)

            # Adjust fastest_realtime win
            if 'fastest_realtime' not in scores or log['dur'] < scores[
                    'fastest_realtime']['dur']:
                scores['fastest_realtime'] = log

            # Adjust fastest_turncount win
            if 'fastest_turncount' not in scores or log['turn'] < scores[
                    'fastest_turncount']['turn']:
                scores['fastest_turncount'] = log

            # Increment god_wins
            if god not in scores['god_wins']:
                scores['god_wins'][god] = 1
                if len(PLAYABLE_GODS.difference(scores['god_wins'].keys(
                ))) == 0:
                    achievements['polytheist'] = True
            else:
                scores['god_wins'][god] += 1

            # Increment race_wins
            if race not in scores['race_wins']:
                scores['race_wins'][race] = 1
                if len(PLAYABLE_RACES.difference(scores['race_wins'].keys(
                ))) == 0:
                    achievements['greatplayer'] = True
            else:
                scores['race_wins'][race] += 1

            # Increment role_wins
            if role not in scores['role_wins']:
                scores['role_wins'][role] = 1
                if len(PLAYABLE_ROLES.difference(scores['role_wins'].keys(
                ))) == 0 and 'greatplayer' in achievements:
                    achievements['greaterplayer'] = True
            else:
                scores['role_wins'][role] += 1

            # Adjust avg_win stats
            if 'avg_win_ac' not in scores:
                scores['avg_win_ac'] = log['ac']
            else:
                scores['avg_win_ac'] += (
                    log['ac'] - scores['avg_win_ac']) / wins
            if 'avg_win_ev' not in scores:
                scores['avg_win_ev'] = log['ev']
            else:
                scores['avg_win_ev'] += (
                    log['ev'] - scores['avg_win_ev']) / wins
            if 'avg_win_sh' not in scores:
                scores['avg_win_sh'] = log['sh']
            else:
                scores['avg_win_sh'] += (
                    log['sh'] - scores['avg_win_sh']) / wins

            # Adjust win-based achievements
            if wins == 10:
                achievements['goodplayer'] = True

            if wins == 100:
                achievements['centuryplayer'] = True

            if log['potionsused'] == 0 and log['scrollsused'] == 0:
                if 'no_potion_or_scroll_win' not in achievements:
                    achievements['no_potion_or_scroll_win'] = 1
                else:
                    achievements['no_potion_or_scroll_win'] += 1

            if 'zigdeepest' in log and log['zigdeepest'] == '27':
                if 'cleared_zig' not in achievements:
                    achievements['cleared_zig'] = 1
                else:
                    achievements['cleared_zig'] += 1

        else:

            # Increment boring_games
            if log['ktyp'] in ('leaving', 'quitting'):
                scores['boring_games'] += 1

        # Adjust winrate
        scores['winrate'] = wins / scores['games']

        # Adjust highscores
        if 'highscore' not in scores or score > scores['highscore']['sc']:
            scores['highscore'] = log

        # if race not in race_highscores or score > race_highscores[race]['sc']:
        # race_highscores[race] = log

        # if role not in role_highscores or score > role_highscores[role]['sc']:
        # role_highscores[role] = log

        # if char not in combo_highscores or score > combo_highscores[char][
        #         'sc']:
        # combo_highscores[char] = log

        # Increment total_score
        scores['total_score'] += score

        # Adjust avg_score
        scores['avg_score'] = scores['total_score'] / scores['games']

        # Adjust last_5_games
        scores['last_5_games'].append(log)

        # Adjust boring_rate
        scores['boring_rate'] = scores['boring_games'] / scores['games']

        model.set_player_score_data(name, scores)

    end = time.time()
    print("Scoring took", end - start, "seconds")
