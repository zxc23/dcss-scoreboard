"""Handle reading logfiles and parsing them."""

import os
import re
import time
import multiprocessing
import traceback

import sqlalchemy.exc

import scoreboard.constants as const
import scoreboard.model as model
import scoreboard.orm as orm

# Logfile format escapes : as ::, so we use re.split
# instead of the naive line.split(':')
LINE_SPLIT_PATTERN = re.compile('(?<!:):(?!:)')


class LogImportError(Exception):
    pass


def calculate_game_gid(game):
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (game['name'], game['src'], game['start'])


def candidate_logfiles(logdir):
    """Yield (logfile, src) tuples from logdir."""
    for d in os.scandir(logdir):
        if not d.is_dir():
            continue
        src = d.name
        src_path = os.path.join(logdir, src)
        print("Loading logfiles from %s" % src_path)
        for f in os.scandir(src_path):
            f_path = os.path.join(src_path, f.name)
            if not f.is_file() or f.stat().st_size == 0:
                continue
            elif re.search(const.MILESTONE_REGEX, f.name):
                # XXX to be handled later
                continue
            elif re.search(const.LOGFILE_REGEX, f.name):
                yield (f_path, src)
            else:
                print("Skipping unknown file {}".format(f.name))


def load_logfiles(logdir):
    """Read logfiles and parse their data.

    Logfiles are kept in a directory with structure:
    logdir/{src}/{log or milestone file}.
    """
    print("Loading all logfiles")
    start = time.time()
    p = multiprocessing.Pool()
    jobs = []
    for candidate in candidate_logfiles(logdir):
        jobs.append(p.apply_async(load_logfile, candidate))
        # load_logfile(*candidate)
    for job in jobs:
        job.get()
    end = time.time()
    print("Loaded logfiles in %s secs" % round(end - start, 2))


def load_logfile(logfile, src):
    """Load a single logfile into the database."""
    if os.stat(logfile).st_size == 0:
        return 0
    start = time.time()
    lines = 0
    new_games = 0
    s = orm.get_session()
    # How many lines have we already processed?
    # We store the data as bytes rather than lines since file.seek is fast
    seek_pos = model.get_logfile_progress(s, logfile).bytes_parsed

    print("Reading %s%s... " % (logfile, (" from byte %s" % seek_pos)
                                if seek_pos else ''))
    s = orm.get_session()
    f = open(logfile, encoding='utf-8')
    f.seek(seek_pos)
    for line in f:
        lines += 1
        # skip blank lines
        if not line.strip():
            continue
        try:
            handle_line(s, line, src)
        except LogImportError:
            print("Couldn't import %s. Exception follows:" % line)
            print(traceback.format_exc())
        else:
            new_games += 1
    s.commit()
    # Save the new number of lines processed in the database
    model.save_logfile_progress(s, logfile, f.tell())
    end = time.time()
    msg = "Finished reading {f} ({l} new lines, {g} new games) in {s} secs"
    print(msg.format(f=logfile, l=lines, g=new_games, s=round(end - start, 2)))


def handle_line(s, line, src):
    """Given a line, parse it and save it into the database.

    Returns True if the line was successfully parsed and added to the database.
    """
    game = parse_line(line, src)
    # Check we got a game back
    if game is None:
        return False
    # Store the game in the database
    tries = 0
    success = False
    while not success:
        try:
            # TODO should use model.add_games
            # Probably via an internal function that batches
            model.add_game(s, game)
        except model.DBError as e:
            problem = True
            # print("Error adding game, rolling back (%s): %s" % (e.__cause__, game))
            s.rollback()
            tries += 1
            if tries == 3:
                raise LogImportError from e
        else:
            success = True
    return success


def parse_field(k, v):
    """Convert field data into the correct data type.

    Integer fields are stored as ints, everything else string.
    """
    # A few games have junk surrounding a field, like \n or \x00. Trim it.
    k = k.strip()
    v = v.strip()
    # Name field is sometimes parseable as an int
    if k != 'name':
        try:
            v = int(v)
        except ValueError:
            pass
    if isinstance(v, str):
        v = v.replace("::", ":")  # Undo logfile escaping
    return k, v


def parse_line(line, src):
    """Read a single logfile line and insert it into the database.

    If the game is not valid, None is returned. Invalid games could be:
        * a non-vanilla crawl game (eg sprint or zotdef)
        * Corrupt data

    """
    # Early warning of corruption
    if '\x00' in line:
        return None

    game = {'src': src}

    # Parse the log's raw field data
    for field in re.split(LINE_SPLIT_PATTERN, line):
        if not field.strip():
            continue
        fields = field.split('=', 1)
        if len(fields) != 2:
            raise ValueError("Couldn't parse line (bad field %r), skipping: %r"
                             % (field, line))
        k, v = parse_field(*fields)
        game[k] = v

    # Validate the data
    if 'start' not in game:
        return None
    # We should only parse vanilla dcss games
    if game['lv'] != '0.1':
        return None
    # Create some derived fields
    game['rc'] = game['char'][:2]
    game['bg'] = game['char'][2:]
    game['gid'] = calculate_game_gid(game)
    # Data cleansing
    # Simplify version to 0.17/0.18/etc
    game['v'] = re.match('(0.\d+)', game['v']).group()
    game.setdefault('tmsg', '')
    if 'god' not in game:
        game['god'] = 'Atheist'
    return game
