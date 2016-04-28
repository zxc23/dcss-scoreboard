#!/usr/bin/env python3
"""CLI to run dcss-scoreboard."""

import argparse
import sys

import scoreboard.model
import scoreboard.log_import
import scoreboard.scoring
import scoreboard.write_website


def error(msg):
    """Print an error and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def read_commandline():
    """Parse command line args and validate them."""
    description = "Run DCSS Scoreboard."
    epilog = "Specify DB_USER/DB_PASS environment variables if required."
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('--database',
                        choices=('mysql', 'sqlite'),
                        default='sqlite',
                        help="Specify the database backend  (default: sqlite)")
    parser.add_argument('--rebuild',
                        action='store_true',
                        help="Rebuild the entire database.")
    parser.add_argument('--player',
                        default='',
                        help="Rebuild just this player's scores.")
    parser.add_argument('--skip-log-import',
                        action='store_true',
                        help="Skip log import.")
    parser.add_argument('--skip-scoring',
                        action='store_true',
                        help="Skip scoring.")
    parser.add_argument('--skip-website',
                        action='store_true',
                        help="Skip website generation.")
    args = parser.parse_args()
    if args.rebuild and args.player:
        error("You can't specify --rebuild and --player together.")
    if args.rebuild and args.skip_scoring:
        error("You can't specify --rebuild and --skip-scoring together.")
    if args.player and args.skip_scoring:
        error("You can't specify --player and --skip-scoring together.")
    return args


def main(player=None):
    args = read_commandline()

    scoreboard.model.setup_database(args.database)

    if not args.skip_log_import:
        scoreboard.log_import.load_logfiles()
    if not args.skip_scoring:
        if args.player:
            scoreboard.scoring.rescore_player(args.player)
        scoreboard.scoring.score_games(rebuild=args.rebuild)
    if not args.skip_website:
        scoreboard.write_website.write_website()


if __name__ == '__main__':
    main()
