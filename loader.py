#!/usr/bin/env python3
"""CLI to run dcss-scoreboard."""

import argparse
import sys

import scoreboard.model
import scoreboard.log_import
import scoreboard.scoring
import scoreboard.write_website
import scoreboard.sources

def error(msg):
    """Print an error and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def read_commandline():
    """Parse command line args and validate them."""
    description = "Run DCSS Scoreboard."
    epilog = "Specify DB_USER/DB_PASS environment variables if required."
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('--logdir',
                        help="Override logfile source. Default: logfiles/",
                        default="logfiles")
    parser.add_argument('--urlbase',
                        help="Override website base URL. Default: file:///CWD")
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
    parser.add_argument('--skip-download',
                        action='store_true',
                        help="Skip log download.")
    parser.add_argument('--skip-import',
                        action='store_true',
                        help="Skip log import.")
    parser.add_argument('--skip-scoring',
                        action='store_true',
                        help="Skip scoring.")
    parser.add_argument('--skip-website',
                        action='store_true',
                        help="Skip website generation.")
    parser.add_argument('--rebuild-player-pages',
                        action='store_true',
                        help="Re-write all player pages for the website.")
    args = parser.parse_args()
    if args.rebuild and args.player:
        error("You can't specify --rebuild and --player together.")
    if args.rebuild and args.skip_scoring:
        error("You can't specify --rebuild and --skip-scoring together.")
    if args.player and args.skip_scoring:
        error("You can't specify --player and --skip-scoring together.")
    return args


def main(player=None):
    """Run CLI."""
    args = read_commandline()

    scoreboard.model.setup_database(args.database)

    if not args.skip_download:
        scoreboard.sources.download_sources(args.logdir)
    if not args.skip_import:
        scoreboard.log_import.load_logfiles(logdir=args.logdir)
    if not args.skip_scoring:
        if args.player:
            scoreboard.scoring.rescore_player(args.player)
        players = scoreboard.scoring.score_games(rebuild=args.rebuild)
    if not args.skip_website:
        if args.rebuild_player_pages:
            players = None
        scoreboard.write_website.write_website(urlbase=args.urlbase,
                                               players=players)


if __name__ == '__main__':
    main()
