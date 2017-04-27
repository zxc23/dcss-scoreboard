"""Handle reading logfiles and parsing them."""

import re
import time
import traceback

import sqlalchemy.orm  # for sqlalchemy.orm.session.Session type hints
import requests

import scoreboard.constants as const
import scoreboard.model as model
import scoreboard.modelutils as modelutils
import scoreboard.orm as orm
import scoreboard.util as util

# Logfile format escapes : as ::, so we use re.split
# instead of the naive line.split(':')
LINE_SPLIT_PATTERN = re.compile('(?<!:):(?!:)')


@util.retry(max_tries=3, wait=5)
def request_logfile_lines(url, current_key):
    """Request another batch of logfile lines.

    May raise requests.exceptions.ReadTimeout.
    """
    params = const.LOGFILE_API_GAME_ARGS
    params['offset'] = current_key
    start = time.time()
    r = requests.get(url, params, timeout=15)
    total = time.time() - start
    print("Log API request from offset %s finished in %.1d seconds" %
          (params['offset'], total))
    if r.status_code != 200:
        raise RuntimeError("HTTP response code %s" % r.status_code)
    return r


def load_logfiles(api_url: str) -> None:
    """Read logfiles and parse their data.

    Logfiles are kept in a directory with structure:
    logdir/{src}/{log or milestone file}.
    """
    print("Loading all logfiles")
    start = time.time()
    games = 0
    s = orm.get_session()

    url = api_url
    current_key = model.get_logfile_progress(s, url).current_key

    while True:
        r = request_logfile_lines(url, current_key)
        try:
            response = r.json()
        except Exception:
            print("Failed to decode into json")
            print(r.text)
            raise
        assert response['status'] == 200 and response['message'] == 'OK'

        if not len(response['results']):
            break

        for game in response['results']:
            try:
                add_game(s, game)
            except StandardError as e:
                print("Couldn't add game, skipping: %s" % game)
            else:
                games += 1
            if games % 10000 == 0:
                print("Processed %s games..." % games)

        current_key = response['next_offset']
        model.save_logfile_progress(s, url, current_key)
        s.commit()
    s.commit()
    end = time.time()
    print("Loaded %s new games in %s secs" % (games, round(end - start, 2)))


def add_game(s: sqlalchemy.orm.session.Session, api_game: dict) -> bool:
    """Add a game to the database.

    Returns True if a game was found and successfully added.
    """
    # Validate the data -- some old broken games don't have this field and
    # and should be ignored.
    if 'start' not in api_game['data']:
        print("Couldn't find start in game, skipping (%s)" % api_game['data'])
        return None
    if 'v' not in api_game['data']:
        print("Couldn't find v in game, skipping (%s)" % api_game['data'])
        return None
    if 'char' not in api_game['data']:
        print("Couldn't find char in game, skipping (%s)" % api_game['data'])
        return None
    # We should only parse vanilla dcss games
    if api_game['data']['lv'] != '0.1':
        return None

    game = {}
    game.update(api_game['data'])
    game['gid'] = "%s:%s:%s" % (game['name'], api_game['src_abbr'],
                                game['start'])
    # Data cleansing
    # Simplify version to 0.17/0.18/etc
    game['v'] = re.match(r"(0.\d+)", game['v']).group()
    if 'god' not in game:
        game['god'] = 'Atheist'
    # Normalise old data
    game['god'] = const.GOD_NAME_FIXUPS.get(game['god'], game['god'])
    game['race'] = const.SPECIES_NAME_FIXUPS.get(game['race'], game['race'])
    # Special fixup for Gnome, which was the original Gn, before Gnoll took
    # that species code.
    if game['v'] in ('0.1', '0.2', '0.3', '0.4',
                     '0.5') and game['char'][:2] == 'Gn':
        game['char'] = 'Gm' + game['char'][2:]
    if game['char'][:2] in const.SPECIES_SHORTNAME_FIXUPS:
        oldrace = game['char'][:2]
        newrace = const.SPECIES_SHORTNAME_FIXUPS[oldrace]
        game['char'] = newrace + game['char'][2:]
    if game['char'][2:] in const.BACKGROUND_SHORTNAME_FIXUPS:
        oldbg = game['char'][2:]
        newbg = const.BACKGROUND_SHORTNAME_FIXUPS[oldbg]
        game['char'] = game['char'][:2] + newbg
    game['br'] = const.BRANCH_NAME_FIXUPS.get(game['br'], game['br'])
    game['ktyp'] = const.KTYP_FIXUPS.get(game['ktyp'], game['ktyp'])
    game['rc'] = game['char'][:2]
    game['bg'] = game['char'][2:]

    # Create a dict with the mappings needed for orm.Game objects
    branch = model.get_branch(s, game['br'])
    server = model.get_server(s, api_game['src_abbr'])
    gamedict = {
        'gid': game['gid'],
        'account_id': model.get_account_id(s, game['name'], server),
        'player_id': model.get_player_id(s, game['name']),
        'species_id': model.get_species(s, game['char'][:2]).id,
        'background_id': model.get_background(s, game['char'][2:]).id,
        'god_id': model.get_god(s, game['god']).id,
        'version_id': model.get_version(s, game['v']).id,
        'place_id': model.get_place(s, branch, game['lvl']).id,
        'xl': game['xl'],
        'tmsg': game.get('tmsg', ''),
        'turn': game['turn'],
        'dur': game['dur'],
        'runes': game.get('urune', 0),
        'score': game['sc'],
        'start': modelutils.crawl_date_to_datetime(game['start']),
        'end': modelutils.crawl_date_to_datetime(game['end']),
        'ktyp_id': model.get_ktyp(s, game['ktyp']).id,
        'potions_used': game.get('potionsused', -1),
        'scrolls_used': game.get('scrollsused', -1),
        'dam': game.get('dam', 0),
        'tdam': game.get('tdam', game.get('dam', 0)),
        'sdam': game.get('sdam', game.get('dam', 0)),
    }
    # Store the game in the database
    try:
        model.add_games(s, [gamedict])
    except model.DBError:
        print("Couldn't import %s. Exception follows:" % game)
        print(traceback.format_exc())
        print()
        s.rollback()
        return False
    except model.DBIntegrityError:
        print("Tried to import duplicate game: %s" % game['gid'])
        s.rollback()
        return False
    else:
        # s.commit()
        pass
    return True
