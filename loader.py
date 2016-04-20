#!/usr/bin/env python3

"""CLI to run dcss-scoreboard."""

import argparse

import scoreboard.log_import
import scoreboard.scoring
import scoreboard.write_website

def main():
    scoreboard.log_import.load_logfiles()
    #scoreboard.scoring.rescore_player('zzxc')
    scoreboard.scoring.score_games()
    scoreboard.write_website.write_website()


if __name__ == '__main__':
    main()
