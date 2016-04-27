"""Handle reading logfiles and parsing them."""

import os
import re
import time
import glob

from . import model

# Logfile format escapes : as ::, so we need to split with re.split
# Instead of naive line.split(':')
LINE_SPLIT_PATTERN = '(?<!:):(?!:)'


def calculate_game_gid(game):
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (game['name'], game['src'], game['start'])


def load_logfiles():
    """Read logfiles and parse their data."""
    print("Loading all logfiles")
    start = time.time()
    count = 0
    for logfile in glob.glob("logfiles/*"):
        count += load_logfile(logfile)
    end = time.time()
    print("Loaded logfiles with %s new games in %s secs" %
          (count, round(end - start, 2)))


def load_logfile(logfile):
    """Load a single logfile into the database.

    Returns the number of new games loaded.
    """
    if os.stat(logfile).st_size == 0:
        return 0
    start = time.time()
    # Should be server source, eg cao, cpo, etc
    src = os.path.basename(logfile.split('-', 1)[0])
    lines = 0
    # How many lines have we already processed?
    processed_lines = model.logfile_pos(logfile)
    print("Reading %s%s... " % (logfile, (" from line %s" % processed_lines) if
                                processed_lines else ''))
    for line in open(logfile, encoding='utf-8').readlines():
        lines += 1
        # skip up to the first unprocessed line
        if lines <= processed_lines:
            continue
        # skip blank lines
        if not line:
            continue
        try:
            parse_line(line, src)
        except Exception as e:
            print("Couldn't parse line (%s): %s" % (e, line))
    # Save the new number of lines processed in the database
    model.save_logfile_pos(logfile, lines)
    end = time.time()
    print("Finished reading %s (%s new lines) in %s secs" %
          (logfile, lines - processed_lines, round(end - start, 2)))
    return lines - processed_lines


def parse_line(line, src):
    """Read a single logfile line and insert it into the database."""
    game = {}
    game['src'] = src
    for field in re.split(LINE_SPLIT_PATTERN, line):
        # skip blank fields
        if not field:
            continue
        fields = field.split('=', 1)
        if len(fields) != 2:
            raise ValueError(
                "Couldn't parse line (bad field %s), skipping: %s" %
                (field, line))
        k, v = fields[0], fields[1]
        # Store numbers as int, not str
        try:
            v = int(v)
        except ValueError:
            v = v.replace("::", ":")  # Undo logfile escaping
        game[k] = v
    game['rc'] = game['char'][:2]
    game['bg'] = game['char'][2:]
    if 'god' not in game:
        game['god'] = 'Atheist'
    # Simplify version to 0.17/0.18/etc
    game['v'] = re.match('(0.\d+)', game['v']).group()
    if 'start' not in game:
        print("Couldn't parse this line (missing start), skipping: %s" % line)
        return
    gid = calculate_game_gid(game)
    game['gid'] = gid
    # Store the game in the database
    try:
        model.add_game(gid, game)
    except model.DatabaseError as e:
        print(e)


if __name__ == "__main__":
    load_logfiles()
