#!/usr/bin/env python3
"""CLI to run dcss-scoreboard."""

import argparse
import sys

import scoreboard.sources
import scoreboard.log_import
import scoreboard.orm
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
    parser.add_argument(
        '--logdir',
        help="Override logfile source. Default: logfiles/",
        default="logfiles")
    parser.add_argument(
        '--urlbase', help="Override website base URL. Default: file:///CWD")
    parser.add_argument(
        '--database',
        choices=('sqlite', 'postgres'),
        default='sqlite',
        help="Specify the database backend  (default: sqlite)")
    parser.add_argument(
        '--download-logfiles',
        action='store_true',
        help="Download logfiles first.")
    parser.add_argument(
        '--download-servers',
        nargs='*',
        metavar="SRC",
        help="Only download logfiles from these servers.")
    parser.add_argument(
        '--skip-import', action='store_true', help="Skip log import.")
    parser.add_argument(
        '--skip-scoring', action='store_true', help="Skip scoring.")
    parser.add_argument(
        '--skip-website', action='store_true', help="Skip website generation.")
    parser.add_argument(
        '--rebuild-player-pages',
        action='store_true',
        help="Re-write all player pages for the website.")
    parser.add_argument(
        '--db-credentials', metavar="user:passwd", help="Database credentials")
    args = parser.parse_args()
    return args


def main():
    """Run CLI."""
    args = read_commandline()

    scoreboard.orm.setup_database(args.database, args.db_credentials)

    if args.download_logfiles:
        scoreboard.sources.download_sources(
            args.logdir, servers=args.download_servers)

    if not args.skip_import:
        scoreboard.log_import.load_logfiles(logdir=args.logdir)

    if not args.skip_scoring:
        players = scoreboard.scoring.score_games()
    else:
        players = False

    if not args.skip_website:
        if args.rebuild_player_pages:
            players = None
        scoreboard.write_website.write_website(
            urlbase=args.urlbase, players=players)


if __name__ == '__main__':
    main()
