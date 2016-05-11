"""Handle reading logfiles and parsing them."""

import os
import re
import time
import multiprocessing
import traceback

from . import model

# Logfile format escapes : as ::, so we use re.split
# instead of the naive line.split(':')
LINE_SPLIT_PATTERN = re.compile('(?<!:):(?!:)')
LOGFILE_REGEX = re.compile('(logfile|allgames)')
MILESTONE_REGEX = re.compile('milestone')


def calculate_game_gid(game):
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (game['name'], game['src'], game['start'])


def load_logfiles(logdir):
    """Read logfiles and parse their data.

    Logfiles are kept in a directory with structure:
    logdir/{src}/{log or milestone file}.
    """
    print("Loading all logfiles")
    start = time.time()
    candidates = []
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
            elif re.search(MILESTONE_REGEX, f.name):
                # XXX to be handled later
                continue
            elif re.search(LOGFILE_REGEX, f.name):
                candidates.append((f_path, src))
                # count += load_logfile(f_path, src)
            else:
                print("Skipping unknown file {}".format(f.name))
    p = multiprocessing.Pool()
    jobs = []
    for candidate in candidates:
        jobs.append(p.apply_async(load_logfile, candidate))
        time.sleep(1)  # Stagger start time
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
    # How many lines have we already processed?
    try:
        seek_pos = model.logfile_pos(logfile)
    except model.DatabaseError as e:
        print(e)
        return

    print("Reading %s%s... " % (logfile, (" from pos %s" % seek_pos) if
                                seek_pos else ''))
    f = open(logfile, encoding='utf-8')
    f.seek(seek_pos)
    for line in f:
        lines += 1
        # skip blank lines
        if not line:
            continue
        if handle_line(line, src):
            new_games += 1
    # Save the new number of lines processed in the database
    model.save_logfile_pos(logfile, f.tell())
    end = time.time()
    msg = "Finished reading {f} ({l} new lines, {g} new games) in {s} secs"
    print(msg.format(f=logfile,
                     l=lines,
                     g=new_games,
                     s=round(end - start, 2)))


def handle_line(line, src):
    """Given a line, parse it and save it into the database.

    Returns True if the line was successfully parsed and added to the database.
    """
    try:
        game = parse_line(line, src)
    except Exception as e:
        print(traceback.format_exc())
        print("Couldn't parse line: %r" % line)
        return False
    # Check we got a game back
    if game is None:
        return False
    # Store the game in the database
    try:
        model.add_game(game['gid'], game)
    except model.DatabaseError as e:
        print(e)
    except model.DuplicateKeyError:
        return False
    return True


def parse_field(k, v):
    """Convert field data into the correct data type.

    Integer fields are stored as ints, everything else string.
    """
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

    If the game is not a vanilla crawl game (eg sprint or zotdef), None is
    returned.
    """
    game = {}
    game['src'] = src

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
        raise ValueError("Couldn't parse this line (missing start field)" %
                         line)
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


if __name__ == "__main__":
    load_logfiles()
