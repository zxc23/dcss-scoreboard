#!/usr/bin/env python3

import os
import sys
import json
import pprint

OUTDIR = 'dcss-scoreboard-html'

if __name__ == '__main__':
    data = json.loads(open('scoring_data.json').read())

    print("Writing HTML to %s" % OUTDIR)
    os.makedirs(OUTDIR)

    with open(os.path.join(OUTDIR, 'index.htm'), 'w') as f:
        f.write("<h1>Homepage</h1>\n")
        f.write("""<p><a href="highscores.htm">Global Highscores</a></p>\n""")
        f.write("""<p><a href="players.htm">Player Pages</a></p>\n""")

    with open(os.path.join(OUTDIR, 'highscores.htm'), 'w') as f:
            f.write("<pre>\n")
            pprint.pprint(data['global_stats'], f)
            f.write("</pre>\n")

    player_html_path = os.path.join(OUTDIR, 'players')
    os.makedirs(player_html_path)
    with open(os.path.join(OUTDIR, 'players.htm'), 'w') as f:
        f.write("<h1>All players</h1>\n")
        f.write("<ul>\n")
        for player in data['players'].keys():
            f.write("""<li><a href="players/{player}.htm">{player}</a></li>\n""".format(player=player))
        f.write("</ul>\n")

    for player, stats in data['players'].items():
        outfile = os.path.join(player_html_path, player + '.htm')
        with open(outfile, 'w') as f:
            f.write("<h1>%s's stats<br>\n" % player)
            f.write("<pre>\n")
            pprint.pprint(stats, f)
            f.write("</pre>\n")
