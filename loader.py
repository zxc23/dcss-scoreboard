#!/usr/bin/env python3
"""CLI to run dcss-scoreboard."""

import argparse
import sys

import scoreboard.log_import
import scoreboard.orm
import scoreboard.scoring
import scoreboard.write_website


def error(msg: str) -> None:
    """Print an error and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def read_commandline() -> argparse.Namespace:
    """Parse command line args and validate them."""
    description = "Run DCSS Scoreboard."
    epilog = "Specify DB_USER/DB_PASS environment variables if required."
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    DEFAULT_API = "https://api.crawl.project357.org/event"
    parser.add_argument(
        "--game-api",
        default=DEFAULT_API,
        help="Specify a custom game API url. Set blank to skip API use. Default: %s"
        % DEFAULT_API,
    )
    parser.add_argument(
        "--urlbase",
        default=None,
        help="Override website base URL. Default: file:///CWD",
    )
    parser.add_argument(
        "--database",
        choices=("sqlite", "postgres"),
        default="sqlite",
        help="Specify the database backend  (default: sqlite)",
    )
    parser.add_argument(
        "--database-path",
        default="database.db3",
        help="Database path (for sqlite). Default: database.db3",
    )
    parser.add_argument("--skip-scoring", action="store_true", help="Skip scoring.")
    parser.add_argument(
        "--skip-website", action="store_true", help="Skip website generation."
    )
    parser.add_argument(
        "--rebuild-player-pages",
        action="store_true",
        help="Re-write all player pages for the website.",
    )
    parser.add_argument(
        "--players",
        nargs="+",
        metavar="PLAYER",
        help="Re-write the specified player pages.",
    )
    parser.add_argument(
        "--extra-player-pages",
        metavar="NUM",
        default=0,
        type=int,
        help="(Re-)Generate pages for an additional NUM players (least recently updated first)",
    )
    parser.add_argument(
        "--db-credentials",
        metavar="user:passwd",
        help="Database credentials",
        default="",
    )
    args = parser.parse_args()
    return args


def main() -> None:
    """Run CLI."""
    args = read_commandline()

    scoreboard.orm.setup_database(
        database=args.database, path=args.database_path, credentials=args.db_credentials
    )

    if args.game_api:
        scoreboard.log_import.load_logfiles(api_url=args.game_api)

    if not args.skip_scoring:
        players = scoreboard.scoring.score_games()
    else:
        players = None

    if not args.skip_website:
        if args.rebuild_player_pages:
            players = None
        if args.players:
            if players:
                players.update(args.players)
            else:
                players = args.players
        scoreboard.write_website.write_website(
            urlbase=args.urlbase,
            players=players,
            extra_player_pages=args.extra_player_pages,
        )


if __name__ == "__main__":
    main()
