#!/usr/bin/env python3

import re
from collections import deque
import time
import json
from operator import itemgetter
import glob

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
    
    # Logfiles to parse
    logfiles = [f for f in glob.glob("*logfiles*.txt")]
    
    # All logs
    logs = []

    # Player data
    players = {}

    # Global stats
    race_highscores = {}
    role_highscores = {}
    combo_highscores = {}
    streaks = []
    active_streaks = []
    
    # Output data
    output = {'players': players, 'global_stats': {'race_highscores': race_highscores,
    'role_highscores': role_highscores, 'combo_highscores': combo_highscores, 
    'streaks': streaks, 'active_streaks': active_streaks}}
    
    logs = parse_logfiles(logfiles)
    calc_stats(logs, players, race_highscores, role_highscores, combo_highscores, streaks, active_streaks)
    write_output(output, 'scoring_data.json')
    print('Completed in', time.time() - start_time, 'seconds')
    
    
def deque_default(obj):
    if isinstance(obj, deque):
        return list(obj)
    raise TypeError


def parse_logfiles(logfiles):
    unsorted = []
    pat = '(?<!:):(?!:)' # logfile format escapes : as ::, so we need to split with re.split instead of naive line.split(':')
    for logfile in logfiles:
        for line in open(logfile).readlines():
            if not line:  # skip blank lines
                continue
            log = {}
            for field in re.split(pat, line):
                if not field:  # skip blank fields
                    continue
                k, v = field.split('=', 1)
                log[k] = v
            unsorted.append(log)
            
    # Sort logs by 'end' field
    return sorted(unsorted, key=itemgetter('end'))
     
     
def calc_stats(logs, players, race_highscores, role_highscores, combo_highscores, streaks, active_streaks):
    for log in logs:

        # Log vars
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
            players[name] = {'wins': [], 'games': 0, 'winrate': 0, 'total_score': 0, 
            'avg_score': 0, 'last_5_games': deque([], 5), 'boring_games': 0, 
            'boring_rate': 0, 'god_wins': {}, 'race_wins': {}, 'role_wins': {}, 
            'achievements': {}}
        player = players[name]
        
        # Player vars
        achievements = player['achievements']
        wins = len(player['wins'])
            
        # Increment games
        player['games'] += 1
        
        # Increment wins
        if log['ktyp'] == 'winning':
            player['wins'].append(log)
            
            # Adjust fastest_realtime win
            if 'fastest_realtime' not in player or log['dur'] < player['fastest_realtime']['dur']:
                player['fastest_realtime'] = log
            
            # Adjust fastest_turncount win
            if 'fastest_turncount' not in player or log['turn'] < player['fastest_turncount']['turn']:
                player['fastest_turncount'] = log
                
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
            if 'avg_win_ac' not in player:
                player['avg_win_ac'] = int(log['ac'])
            else:
                player['avg_win_ac'] += (int(log['ac']) - player['avg_win_ac']) / wins
            if 'avg_win_ev' not in player:
                player['avg_win_ev'] = int(log['ev'])
            else:
                player['avg_win_ev'] += (int(log['ev']) - player['avg_win_ev']) / wins
            if 'avg_win_sh' not in player:
                player['avg_win_sh'] = int(log['sh'])
            else:
                player['avg_win_sh'] += (int(log['sh']) - player['avg_win_sh']) / wins
                
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
                player['boring_games'] += 1
            
        # Adjust winrate
        player['winrate'] = wins / player['games'] 
        
        # Adjust highscores
        if 'highscore' not in player or score > int(player['highscore']['sc']):
            player['highscore'] = log
            
        if race not in race_highscores or score > int(race_highscores[race]['sc']):
            race_highscores[race] = log

        if role not in role_highscores or score > int(role_highscores[role]['sc']):
            role_highscores[role] = log
            
        if char not in combo_highscores or score > int(combo_highscores[char]['sc']):
            combo_highscores[char] = log
            
        # Increment total_score
        player['total_score'] += score
        
        # Adjust avg_score
        player['avg_score'] = player['total_score'] / player['games']
        
        # Adjust last_5_games
        player['last_5_games'].append(log)
        
        # Adjust boring_rate
        player['boring_rate'] = player['boring_games'] / player['games']
        
    calc_streaks(logs, players, streaks, active_streaks)


def calc_streaks(logs, players, streaks, active_streaks):
    active_streak_players = {}
    
    # Iterate through logs to find all streaks
    for log in logs:
        player = log['name']
    
        # If game win
        if log['ktyp'] == 'winning':
        
            # Make active streak list
            if player not in active_streak_players:
                active_streak_players[player] = []
            
            # Start active streak if no active streak
            if len(active_streak_players[player]) == 0:
                active_streak_players[player].append(log)
                continue
            
            # Extend active streak only if win started after previous game end
            if log['start'][:-1] > active_streak_players[player][-1]['end']:
                active_streak_players[player].append(log)
            
        # If game loss
        else:
        
            # Skip players with no active streak
            if player not in active_streak_players:
                continue
                
            # Finalise streaks of 2 or more wins
            if len(active_streak_players[player]) >= 2:
            
                # TODO: Insert anti-griefing code here
                
                # Place streak in streaks
                streaks.append({'player': player, 
                'wins': active_streak_players[player], 
                'streak_breaker': log, 
                'start': active_streak_players[player][0]['start'], 
                'end': active_streak_players[player][-1]['end']})
               
            # Reset active streak    
            active_streak_players[player] = []
            
    # Add streaks to unsorted lists
    for name, streak in active_streak_players.items():
    
        # Keep only streaks of 2 or more wins
        if len(streak) < 2:
            continue
            
        active_streaks.append(streak)
        streaks.append({'player': name, 
            'wins': streak, 
            'start': streak[0]['start'], 
            'end': streak[-1]['end']})
    
    # Sort streaks
    active_streaks.sort(key=lambda x: (-len(x), x[-1]['end']))
    streaks.sort(key=lambda x: (-len(x['wins']), x['end']))
    
    # Print streak summary
    #for streak in streaks:
        #print(streak['player'], len(streak['wins']), streak['end']) 


def write_output(output, filename):
    f = open(filename, 'w')
    json.dump(output, f, default=deque_default)
    print('Output written to', filename)
    f.close()


if __name__ == '__main__':
    main()
    