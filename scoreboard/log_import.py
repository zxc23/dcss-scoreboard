"""Handle reading logfiles and parsing them."""

import collections
import os
import re
import time
import traceback
from typing import Iterable, Optional, Union, Tuple

import sqlalchemy.orm  # for sqlalchemy.orm.session.Session type hints

import scoreboard.constants as const
import scoreboard.model as model
import scoreboard.modelutils as modelutils
import scoreboard.orm as orm

# Logfile format escapes : as ::, so we use re.split
# instead of the naive line.split(':')
LINE_SPLIT_PATTERN = re.compile('(?<!:):(?!:)')


class LogImportError(Exception):
    """Simple error wrapper."""
    pass


def calculate_game_gid(game: dict) -> str:
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (game['name'], game['src'], game['start'])


Logfile = collections.namedtuple('Logfile', ('path', 'src'))
LogfileLine = collections.namedtuple('LogfileLine', ('data', 'src'))


def candidate_logfiles(logdir: str) -> Iterable[Logfile]:
    """Yield (logfile, src) tuples from logdir."""
    # Sorting by name is purely for beauty
    # But maybe also a little to improve determinism
    for d in sorted(os.scandir(logdir), key=lambda i: i.name.lower()):
        if not d.is_dir():
            continue
        src = d.name
        src_path = os.path.join(logdir, src)
        print("Loading logfiles from %s" % src_path)
        for f in sorted(os.scandir(src_path), key=lambda i: i.name.lower()):
            f_path = os.path.join(src_path, f.name)
            if not f.is_file() or f.stat().st_size == 0:
                continue
            elif re.search(const.MILESTONE_REGEX, f.name):
                # XXX to be handled later
                continue
            elif re.search(const.LOGFILE_REGEX, f.name):
                yield Logfile(f_path, src)
            else:
                print("Skipping unknown file {}".format(f.name))


def load_logfiles(logdir: str) -> None:
    """Read logfiles and parse their data.

    Logfiles are kept in a directory with structure:
    logdir/{src}/{log or milestone file}.
    """
    print("Loading all logfiles")
    start = time.time()
    lines = 0
    s = orm.get_session()
    for logfile in candidate_logfiles(logdir):
        for line in read_logfile(s, logfile):
            game = parse_logfile_line(s, line)
            add_game(s, game)
            lines += 1
            if lines % 10000 == 0:
                print("Processed %s lines..." % lines)
                s.commit()
    s.commit()
    end = time.time()
    print("Loaded logfiles in %s secs" % round(end - start, 2))


def read_logfile(s: sqlalchemy.orm.session.Session, logfile:
                 Logfile) -> Iterable[LogfileLine]:
    if os.stat(logfile.path).st_size == 0:
        return StopIteration
    start = time.time()
    # How many lines have we already processed?
    # We store the data as bytes rather than lines since file.seek is fast
    seek_pos = model.get_logfile_progress(s, logfile.path).bytes_parsed

    print("Reading %s from byte %s... " % (logfile.path, seek_pos))
    f = open(logfile.path, encoding='utf-8')
    f.seek(seek_pos)

    lines = 0
    line = True
    while line:
        line = f.readline()
        if line is '':
            break
        lines += 1
        # skip blank lines
        if not line.strip():
            continue
        yield LogfileLine(line, logfile.src)
        if lines % 10000 == 0:
            model.save_logfile_progress(s, logfile.path, f.tell())
    model.save_logfile_progress(s, logfile.path, f.tell())
    end = time.time()
    msg = "Finished reading {f} ({l} new lines) in {s} secs"
    print(msg.format(f=logfile.path, l=lines, s=round(end - start, 2)))


def parse_logfile_line(s: sqlalchemy.orm.session.Session, line:
                       LogfileLine) -> Optional[dict]:
    """Read a single logfile line and insert it into the database.

    If the game is not valid, None is returned. Invalid games could be:
        * a non-vanilla crawl game (eg sprint or zotdef)
        * Corrupt data

    """
    # Early warning of corruption
    if '\x00' in line.data:
        return None

    game = {'src': line.src}

    # Parse the log's raw field data
    for field in re.split(LINE_SPLIT_PATTERN, line.data):
        if not field.strip():
            continue
        k, v = parse_field(field)
        game[k] = v

    # Validate the data -- some old broken games don't have this field and
    # and should be ignored.
    if 'start' not in game:
        return None
    if 'v' not in game:
        print("Found game without version tag, skipping. Line: %s, Game: %s" % (line.data, game))
        return None
    # We should only parse vanilla dcss games
    if game['lv'] != '0.1':
        return None
    game['gid'] = calculate_game_gid(game)
    # Data cleansing
    # Simplify version to 0.17/0.18/etc
    game['v'] = re.match(r"(0.\d+)", game['v']).group()
    if 'god' not in game:
        game['god'] = 'Atheist'
    # Normalise old data
    game['god'] = const.GOD_NAME_FIXUPS.get(game['god'], game['god'])
    game['race'] = const.SPECIES_NAME_FIXUPS.get(game['race'], game['race'])
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
    server = model.get_server(s, game['src'])
    gamedict = {
        'gid': game['gid'],
        'account_id': model.get_account_id(s, game['name'], server),
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

    return gamedict


def add_game(s: sqlalchemy.orm.session.Session, game: Optional[dict]) -> bool:
    if game is None:
        return False
    # Store the game in the database
    try:
        model.add_games(s, [game])
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


def parse_field(field: str) -> Tuple[str, Union[int, str]]:
    """Convert field value into the correct data type.

    Integer fields are stored as ints, everything else string.
    """
    if '=' not in field:
        raise ValueError("Field is missing a '='" % field)
    k, v = field.split('=', 1)
    # A few games have junk surrounding a field, like \n or \x00. Trim it.
    k = k.strip()
    v = v.strip()
    # Name should always be a string
    if k != 'name':
        try:
            parsed_v = int(v)
        except ValueError:
            parsed_v = v
    else:
        parsed_v = v
    if isinstance(parsed_v, str):
        parsed_v = v.replace("::", ":")  # Undo logfile escaping
    return k, parsed_v
