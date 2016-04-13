#!/usr/bin/env python3

import re
from collections import deque
import time

start = time.time()
all_logs = []
players = {}
race_highscores = {}
role_highscores = {}
combo_highscores = {}
all_playable_races = {'Ce', 'DD', 'DE', 'Dg', 'Ds', 'Dr', 'Fe', 'Fo', 'Gh', 
'Gr', 'HE', 'HO', 'Ha', 'Hu', 'Ko', 'Mf', 'Mi', 'Mu', 'Na', 'Op', 'Og', 'Sp', 
'Te', 'Tr', 'VS', 'Vp'}
all_playable_roles = {'AE', 'AK', 'AM', 'Ar', 'As', 'Be', 'CK', 'Cj', 'EE', 
'En', 'FE', 'Fi', 'Gl', 'Hu', 'IE', 'Mo', 'Ne', 'Sk', 'Su', 'Tm', 'VM', 'Wn', 
'Wr', 'Wz'}
all_playable_gods = {'Ashenzari', 'Beogh', 'Cheibriados', 'Dithmenos', 'Elyvilon',
'Fedhas', 'Gozag', 'Jiyva', 'Kikubaaqudgha', 'Lugonu', 'Makhleb', 'Nemelex Xobeh',
'Okawaru', 'Pakellas', 'Qazlal', 'Ru', 'Sif Muna', 'the Shining One', 'Trog', 
'Vehumet', 'Xom', 'Yredelemnul', 'Zin'}

# Clean up logfiles
pat = '(?<!:):(?!:)' # logfile format escapes : as ::, so we need to split with re.split instead of naive line.split(':')
for line in open('dcss-logfiles-trunk.txt').readlines():
    if not line:  # skip blank lines
        continue
    logfile = {}
    for field in re.split(pat, line):
        if not field:  # skip blank fields
            continue
        #print(field)
        k, v = field.split('=', 1)
        logfile[k] = v
    #print(logfile)
    all_logs.append(logfile)

# Parse stats in each logfile
for log in all_logs:

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
        'achievements': set(), 'last_game_end': 0}
        
    # Increment games
    players[name]['games'] += 1
    
    # Increment wins
    if log['ktyp'] == 'winning':
        players[name]['wins'] += 1
        
        # Adjust fastest_realtime
        if players[name]['fastest_realtime'] == 'N/A' or log['dur'] < players[name]['fastest_realtime']:
             players[name]['fastest_realtime'] = log['dur']
        
        # Adjust fastest_turncount
        if players[name]['fastest_turncount'] == 'N/A' or log['turn'] < players[name]['fastest_turncount']:
             players[name]['fastest_turncount'] = log['turn']
             
        # Increment active_streak
        players[name]['active_streak'] += 1
        
        # Adjust longest_streak
        if players[name]['active_streak'] > players[name]['longest_streak']:
            players[name]['longest_streak'] = players[name]['active_streak']
            
        # Increment god_wins            
        if god not in players[name]['god_wins']:
            players[name]['god_wins'][god] = 1
            if len(all_playable_gods.difference(players[name]['god_wins'].keys())) == 0:
                players[name]['achievements'].add('polytheist')
        else:
            players[name]['god_wins'][god] += 1
            
        # Increment race_wins
        if race not in players[name]['race_wins']:
            players[name]['race_wins'][race] = 1
            if len(all_playable_races.difference(players[name]['race_wins'].keys())) == 0:
                players[name]['achievements'].add('greatplayer')
        else:
            players[name]['race_wins'][race] += 1
            
        # Increment role_wins
        if role not in players[name]['role_wins']:
            players[name]['role_wins'][role] = 1
            if len(all_playable_roles.difference(players[name]['role_wins'].keys())) == 0 \
            and 'greatplayer' in players[name]['achievements']:
                players[name]['achievements'].add('greaterplayer')
        else:
            players[name]['role_wins'][role] += 1
            
        # Adjust avg_win stats
        if players[name]['avg_win_ac'] == 'N/A':
            players[name]['avg_win_ac'] = int(log['ac'])
        else:
            players[name]['avg_win_ac'] += (int(log['ac']) - players[name]['avg_win_ac']) / players[name]['wins']
        if players[name]['avg_win_ev'] == 'N/A':
            players[name]['avg_win_ev'] = int(log['ev'])
        else:
            players[name]['avg_win_ev'] += (int(log['ev']) - players[name]['avg_win_ev']) / players[name]['wins']
        if players[name]['avg_win_sh'] == 'N/A':
            players[name]['avg_win_sh'] = int(log['sh'])
        else:
            players[name]['avg_win_sh'] += (int(log['sh']) - players[name]['avg_win_sh']) / players[name]['wins']
            
        # Adjust win-based achievements
        if players[name]['wins'] == 10:
            players[name]['achievements'].add('goodplayer')
            
        if players[name]['wins'] == 100:
            players[name]['achievements'].add('centuryplayer')
            
        if log['potionsused'] == 0 and log['scrollsused'] == 0:
            players[name]['achievements'].add('no_potion_or_scroll_win')
            
        if 'zigdeepest' in log and log['zigdeepest'] == '27':
            players[name]['achievements'].add('cleared_zig')
       
    # Reset active_streak on non-win
    else:
        players[name]['active_streak'] = 0
        
        # Increment boring_games
        if log['ktyp'] in ('leaving', 'quitting'):
            players[name]['boring_games'] += 1
        
    # Adjust winrate
    players[name]['winrate'] = players[name]['wins'] / players[name]['games'] 
    
    # Adjust highscores
    if score > players[name]['highscore']:
        players[name]['highscore'] = score
        
    if race not in race_highscores or score > race_highscores[race]:
        race_highscores[race] = score

    if role not in role_highscores or score > role_highscores[role]:
        role_highscores[role] = score
        
    if char not in combo_highscores or score > combo_highscores[char]:
        combo_highscores[char] = score
        
    # Increment total_score
    players[name]['total_score'] += score
    
    # Adjust avg_score
    players[name]['avg_score'] = players[name]['total_score'] / players[name]['games']
    
    # Adjust last_5_games_scores
    players[name]['last_5_games_scores'].appendleft(score)
    
    # Adjust boring_rate
    players[name]['boring_rate'] = players[name]['boring_games'] / players[name]['games'] 
    
    # Adjust last_game_end
    players[name]['last_game_end'] = log['end']
        
testplayer = 'chequers'
print(testplayer + "'s stats:")
print(players[testplayer])
print(time.time() - start, 'seconds')