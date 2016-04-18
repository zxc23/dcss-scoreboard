"""Handle reading logfiles and parsing them."""

import os
import re
import time
import glob
import multiprocessing

from . import model
from . import constants


def calculate_game_gid(log):
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (log['name'], log['src'], log['start'])


def load_logfiles():
    """Read logfiles and parse their data."""
    print("Loading all logfiles")
    start = time.time()
    p = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    # p.map(load_logfile, glob.glob("logfiles/*"))
    jobs = []
    for logfile in glob.glob("logfiles/*"):
        jobs.append(p.apply_async(load_logfile, (logfile,)))
    for async_job in jobs:
        async_job.wait()
    end = time.time()
    print("Loaded all logfiles in %s secs" % round(end - start, 2))


def load_logfile(logfile):
    """Load a single logfile into the database."""
    if os.stat(logfile).st_size == 0:
        return
    # logfile format escapes : as ::, so we need to split with re.split
    # instead of naive line.split(':')
    pat = '(?<!:):(?!:)'
    start = time.time()
    # should be server source, eg cao, cpo, etc
    src = os.path.basename(logfile.split('-', 1)[0])
    lines = 0
    # How many lines have we already processed?
    processed_lines = model.get_log_pos(logfile)
    print("Reading %s%s... " % (logfile,
                                (" from line %s" % processed_lines) if
                                processed_lines else ''))
    for line in open(logfile).readlines():
        lines += 1
        # skip up to the first unprocessed line
        if lines <= processed_lines:
            continue
        # skip blank lines
        if not line:
            continue

        log = {}
        log['src'] = src
        for field in re.split(pat, line):
            # skip blank fields
            if not field:
                continue
            k, v = field.split('=', 1)
            # Store numbers as int, not str
            try:
                v = int(v)
            except ValueError:
                v = v.replace("::", ":")  # Undo logfile escaping
            log[k] = v
        log['rc'] = log['char'][:2]
        log['bg'] = log['char'][2:]
        if 'god' not in log:
            log['god'] = 'Atheist'
        log['god'] = constants.GOD_NAME_FIXUPS.get(log['god'], log['god'])
        gid = calculate_game_gid(log)
        # Store the game in the database
        try:
            model.add_game(gid, log)
        except model.DatabaseError as e:
            print(e)
    # Save the new number of lines processed in the database
    model.save_log_pos(logfile, lines)
    end = time.time()
    print("Finished reading %s (%s new lines) in %s secs" % (logfile, lines - processed_lines,
                                              round(end - start, 2)))


if __name__ == "__main__":
    load_logfiles()
