#!/usr/bin/env python3

import dcss_scoreboard
import dcss_scoreboard.log_import
import dcss_scoreboard.scoring

dcss_scoreboard.log_import.load_logfiles()
dcss_scoreboard.scoring.score_games()
