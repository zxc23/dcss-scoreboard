"""Handle reading logfiles and parsing them."""

import os
import re

from . import model


def calculate_game_gid(log):
    """Calculate GID for a game. Sequell compatible."""
    return "%s:%s:%s" % (log['name'], log['src'], log['start'])


def load_logfiles():
    """Read logfiles and parse their data.

    XXX: should be given a filename to read, not figure it out ourselves.
    """
    import glob
    # logfile format escapes : as ::, so we need to split with re.split
    # instead of naive line.split(':')
    pat = '(?<!:):(?!:)'
    for logfile in glob.glob("logfiles/*"):
        # should be server source, eg cao, cpo, etc
        src = os.path.basename(logfile.split('-', 1)[0])
        if os.stat(logfile).st_size == 0:
            continue
        lines = 0
        # How many lines have we already processed?
        processed_lines = model.get_log_pos(logfile)
        print("Reading %s%s... " % (logfile,
                                    (" from line %s" % processed_lines) if
                                    processed_lines else ''),
              end='')
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
            gid = calculate_game_gid(log)
            # Store the game in the database
            try:
                model.add_game(gid, log)
            except model.DatabaseError as e:
                print(e)
        print("done (%s new lines)" % (lines - processed_lines))
        # Save the new number of lines processed in the database
        model.save_log_pos(logfile, lines)


if __name__ == "__main__":
    load_logfiles()
