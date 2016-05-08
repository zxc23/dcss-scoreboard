"""Handle reading logfiles and parsing them."""

import os
import re
import time

from . import model

# Logfile format escapes : as ::, so we use re.split
# instead of the näive line.split(':')
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
    count = 0
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
                count += load_logfile(f_path, src)
            else:
                print("Skipping unknown file {}".format(f.name))
    end = time.time()
    print("Loaded logfiles with %s new games in %s secs" %
          (count, round(end - start, 2)))


def load_logfile(logfile, src):
    """Load a single logfile into the database.

    Returns the number of new games loaded.
    """
    if os.stat(logfile).st_size == 0:
        return 0
    start = time.time()
    lines = 0
    # How many lines have we already processed?
    processed_lines = model.logfile_pos(logfile)
    print("Reading %s%s... " % (logfile, (" from line %s" % processed_lines) if
                                processed_lines else ''))
    for line in open(logfile, encoding='utf-8'):
        lines += 1
        if lines == processed_lines + 10:
            break
        # skip up to the first unprocessed line
        if lines <= processed_lines:
            continue
        # skip blank lines
        if not line:
            continue
        try:
            game = parse_line(line, src)
        except Exception as e:
            print("Couldn't parse line (%s): %s" % (e, line))
            continue
        # Check we got a game back
        if game is None:
            continue
        # Store the game in the database
        try:
            model.add_game(game['gid'], game)
        except model.DatabaseError as e:
            print(e)
    # Save the new number of lines processed in the database
    model.save_logfile_pos(logfile, lines)
    end = time.time()
    print("Finished reading %s (%s new lines) in %s secs" %
          (logfile, lines - processed_lines, round(end - start, 2)))
    return lines - processed_lines


def parse_line(line, src):
    """Read a single logfile line and insert it into the database.

    If the game is not a vanilla crawl game (eg sprint or zotdef), None is
    returned.
    """
    game = {}
    game['src'] = src

    # Parse the log's raw field data
    for field in re.split(LINE_SPLIT_PATTERN, line):
        # skip blank fields
        if not field:
            continue
        fields = field.split('=', 1)
        if len(fields) != 2:
            raise ValueError("Couldn't parse line (bad field %s), skipping: %s"
                             % (field, line))
        k, v = fields[0], fields[1]
        # Store numbers as int, not str
        try:
            v = int(v)
        except ValueError:
            v = v.replace("::", ":")  # Undo logfile escaping
        game[k] = v

    # Validate the data
    if 'start' not in game:
        raise ValueError("Couldn't parse this line (missing start field)" %
                         line)
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
