#!/usr/bin/env python3

import re
from collections import deque
import time
import json

ALL_PLAYABLE_RACES = {'Ce', 'DD', 'DE', 'Dg', 'Ds', 'Dr', 'Fe', 'Fo', 'Gh', 
'Gr', 'HE', 'HO', 'Ha', 'Hu', 'Ko', 'Mf', 'Mi', 'Mu', 'Na', 'Op', 'Og', 'Sp', 
'Te', 'Tr', 'VS', 'Vp'}
ALL_PLAYABLE_ROLES = {'AE', 'AK', 'AM', 'Ar', 'As', 'Be', 'CK', 'Cj', 'EE', 
'En', 'FE', 'Fi', 'Gl', 'Hu', 'IE', 'Mo', 'Ne', 'Sk', 'Su', 'Tm', 'VM', 'Wn', 
'Wr', 'Wz'}
ALL_PLAYABLE_GODS = {'Ashenzari', 'Beogh', 'Cheibriados', 'Dithmenos', 'Elyvilon',
'Fedhas', 'Gozag', 'Jiyva', 'Kikubaaqudgha', 'Lugonu', 'Makhleb', 'Nemelex Xobeh',
'Okawaru', 'Pakellas', 'Qazlal', 'Ru', 'Sif Muna', 'the Shining One', 'Trog', 
'Vehumet', 'Xom', 'Yredelemnul', 'Zin'}

def main():
    start_time = time.time()
    
    # All logs
    logs = []

    # Player data
    players = {}

    # Global stats
    race_highscores = {}
    role_highscores = {}
    combo_highscores = {}
    
    # Output data
    output = {'players': players, 'global_stats': {'race_highscores': race_highscores,
    'role_highscores': role_highscores, 'combo_highscores': combo_highscores}}
    
    parse_logfile('dcss-logfiles-trunk.txt', logs)
    calc_stats(logs, players, race_highscores, role_highscores, combo_highscores)
    write_output(output, 'scoring_data.json')
    
    print('Completed in', time.time() - start_time, 'seconds')
    
def deque_default(obj):
    if isinstance(obj, deque):
        return list(obj)
    raise TypeError

def parse_logfile(logfile, output):
    pat = '(?<!:):(?!:)' # logfile format escapes : as ::, so we need to split with re.split instead of naive line.split(':')
    for line in open(logfile).readlines():
        if not line:  # skip blank lines
            continue
        log = {}
        for field in re.split(pat, line):
            if not field:  # skip blank fields
                continue
            #print(field)
            k, v = field.split('=', 1)
            log[k] = v
        #print(log)
        output.append(log)

def calc_stats(logs, players, race_highscores, role_highscores, combo_highscores):
    for log in logs:

        # Local vars
        name = log['name']
        if 'god' in log:
            god = log['god']
        else:
            god = 'no_god'
        score = int(log['sc'])
        race = log['char'][:2]
        role = log['char'][2:]
        char = log['char']
        
        # Make player dictionary
        if name not in players:
            players[name] = {'wins': 0, 'games': 0, 'winrate': 0, 'highscore': 0, 'fastest_realtime': 'N/A', 
            'fastest_turncount': 'N/A', 'total_score': 0, 'avg_score': 0, 'active_streak': 0, 'longest_streak': 0,
            'last_5_games_scores': deque([], 5), 'boring_games': 0, 'boring_rate': 0, 'god_wins': {}, 
            'race_wins': {}, 'role_wins': {}, 'avg_win_ac': 'N/A', 'avg_win_ev': 'N/A', 'avg_win_sh': 'N/A', 
            'achievements': {}, 'last_game_end': 0}
        player = players[name]
            
        # Increment games
        player['games'] += 1
        
        # Increment wins
        if log['ktyp'] == 'winning':
            player['wins'] += 1
            
            # Short vars
            achievements = player['achievements']
            
            # Adjust fastest_realtime
            if player['fastest_realtime'] == 'N/A' or log['dur'] < player['fastest_realtime']:
                player['fastest_realtime'] = log['dur']
            
            # Adjust fastest_turncount
            if player['fastest_turncount'] == 'N/A' or log['turn'] < player['fastest_turncount']:
                player['fastest_turncount'] = log['turn']
                
            # Increment active_streak
            player['active_streak'] += 1
            
            # Adjust longest_streak
            if player['active_streak'] > player['longest_streak']:
                player['longest_streak'] = player['active_streak']
                
            # Increment god_wins            
            if god not in player['god_wins']:
                player['god_wins'][god] = 1
                if len(ALL_PLAYABLE_GODS.difference(player['god_wins'].keys())) == 0:
                    achievements['polytheist'] = True
            else:
                player['god_wins'][god] += 1
                
            # Increment race_wins
            if race not in player['race_wins']:
                player['race_wins'][race] = 1
                if len(ALL_PLAYABLE_RACES.difference(player['race_wins'].keys())) == 0:
                    achievements['greatplayer'] = True
            else:
                player['race_wins'][race] += 1
                
            # Increment role_wins
            if role not in player['role_wins']:
                player['role_wins'][role] = 1
                if len(ALL_PLAYABLE_ROLES.difference(player['role_wins'].keys())) == 0 \
                and 'greatplayer' in achievements:
                    achievements['greaterplayer'] = True
            else:
                player['role_wins'][role] += 1
                
            # Adjust avg_win stats
            if player['avg_win_ac'] == 'N/A':
                player['avg_win_ac'] = int(log['ac'])
            else:
                player['avg_win_ac'] += (int(log['ac']) - player['avg_win_ac']) / player['wins']
            if player['avg_win_ev'] == 'N/A':
                player['avg_win_ev'] = int(log['ev'])
            else:
                player['avg_win_ev'] += (int(log['ev']) - player['avg_win_ev']) / player['wins']
            if player['avg_win_sh'] == 'N/A':
                player['avg_win_sh'] = int(log['sh'])
            else:
                player['avg_win_sh'] += (int(log['sh']) - player['avg_win_sh']) / player['wins']
                
            # Adjust win-based achievements
            if player['wins'] == 10:
                achievements['goodplayer'] = True
                
            if player['wins'] == 100:
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
        
        # Reset active_streak on non-win
        else:
            player['active_streak'] = 0
            
            # Increment boring_games
            if log['ktyp'] in ('leaving', 'quitting'):
                player['boring_games'] += 1
            
        # Adjust winrate
        player['winrate'] = player['wins'] / player['games'] 
        
        # Adjust highscores
        if score > player['highscore']:
            player['highscore'] = score
            
        if race not in race_highscores or score > race_highscores[race]:
            race_highscores[race] = score

        if role not in role_highscores or score > role_highscores[role]:
            role_highscores[role] = score
            
        if char not in combo_highscores or score > combo_highscores[char]:
            combo_highscores[char] = score
            
        # Increment total_score
        player['total_score'] += score
        
        # Adjust avg_score
        player['avg_score'] = player['total_score'] / player['games']
        
        # Adjust last_5_games_scores
        player['last_5_games_scores'].appendleft(score)
        
        # Adjust boring_rate
        player['boring_rate'] = player['boring_games'] / player['games'] 
        
        # Adjust last_game_end
        player['last_game_end'] = log['end']

def write_output(output, filename):
    f = open(filename, 'w')
    json.dump(output, f, default=deque_default)
    print('Output written to', filename)
    f.close()

if __name__ == '__main__':
    main()
    