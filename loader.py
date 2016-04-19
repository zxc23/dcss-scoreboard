#!/usr/bin/env python3

import scoreboard.log_import
import scoreboard.scoring
import scoreboard.write_website

scoreboard.log_import.load_logfiles()
#scoreboard.scoring.rescore_player('zzxc')
#scoreboard.scoring.score_games()
scoreboard.scoring.score_games(rebuild=True)
scoreboard.write_website.write_website()
