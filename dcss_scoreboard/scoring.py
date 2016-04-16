"""Take game data and figure out scoring."""

# from collections import deque

import dcss_scoreboard.model as model

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


def score_games():
    """Update scores with all game's data."""
    print("Scoring all games...")
    scored = 0
    for gid, log in model.games():
        scored += 1
        if scored % 10000 == 0:
            print(scored)
        # print("Scoring", gid)
        # Log vars
        name = log['name']
        if 'god' in log:
            god = log['god']
        else:
            god = 'no_god'
        score = log['sc']
        race = log['char'][:2]
        role = log['char'][2:]

        # Make player dictionary
        scoring = model.get_player_score_data(name)

        # Player vars
        achievements = scoring['achievements']
        wins = len(scoring['wins'])

        # Increment games
        scoring['games'] += 1

        # Increment wins
        if log['ktyp'] == 'winning':
            scoring['wins'].append(log)

            # Adjust fastest_realtime win
            if 'fastest_realtime' not in scoring or log['dur'] < scoring[
                    'fastest_realtime']['dur']:
                scoring['fastest_realtime'] = log

            # Adjust fastest_turncount win
            if 'fastest_turncount' not in scoring or log['turn'] < scoring[
                    'fastest_turncount']['turn']:
                scoring['fastest_turncount'] = log

            # Increment god_wins
            if god not in scoring['god_wins']:
                scoring['god_wins'][god] = 1
                if len(PLAYABLE_GODS.difference(scoring['god_wins'].keys(
                ))) == 0:
                    achievements['polytheist'] = True
            else:
                scoring['god_wins'][god] += 1

            # Increment race_wins
            if race not in scoring['race_wins']:
                scoring['race_wins'][race] = 1
                if len(PLAYABLE_RACES.difference(scoring['race_wins'].keys(
                ))) == 0:
                    achievements['greatplayer'] = True
            else:
                scoring['race_wins'][race] += 1

            # Increment role_wins
            if role not in scoring['role_wins']:
                scoring['role_wins'][role] = 1
                if len(PLAYABLE_ROLES.difference(scoring['role_wins'].keys(
                ))) == 0 and 'greatplayer' in achievements:
                    achievements['greaterplayer'] = True
            else:
                scoring['role_wins'][role] += 1

            # Adjust avg_win stats
            if 'avg_win_ac' not in scoring:
                scoring['avg_win_ac'] = log['ac']
            else:
                scoring['avg_win_ac'] += (
                    log['ac'] - scoring['avg_win_ac']) / wins
            if 'avg_win_ev' not in scoring:
                scoring['avg_win_ev'] = log['ev']
            else:
                scoring['avg_win_ev'] += (
                    log['ev'] - scoring['avg_win_ev']) / wins
            if 'avg_win_sh' not in scoring:
                scoring['avg_win_sh'] = log['sh']
            else:
                scoring['avg_win_sh'] += (
                    log['sh'] - scoring['avg_win_sh']) / wins

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
                scoring['boring_games'] += 1

        # Adjust winrate
        scoring['winrate'] = wins / scoring['games']

        # Adjust highscores
        if 'highscore' not in scoring or score > scoring['highscore']['sc']:
            scoring['highscore'] = log

        # if race not in race_highscores or score > race_highscores[race]['sc']:
        # race_highscores[race] = log

        # if role not in role_highscores or score > role_highscores[role]['sc']:
        # role_highscores[role] = log

        # if char not in combo_highscores or score > combo_highscores[char][
        #         'sc']:
        # combo_highscores[char] = log

        # Increment total_score
        scoring['total_score'] += score

        # Adjust avg_score
        scoring['avg_score'] = scoring['total_score'] / scoring['games']

        # XXX re-add the deque conversion to re-enable this
        # Adjust last_5_games
        # scoring['last_5_games'].append(log)

        # Adjust boring_rate
        scoring['boring_rate'] = scoring['boring_games'] / scoring['games']

        model.set_player_score_data(name, scoring)
