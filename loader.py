#!/usr/bin/env python3

import dcss_scoreboard.log_import
import dcss_scoreboard.scoring
import dcss_scoreboard.write_website

dcss_scoreboard.log_import.load_logfiles()
dcss_scoreboard.scoring.score_games()
dcss_scoreboard.write_website.write_website()
