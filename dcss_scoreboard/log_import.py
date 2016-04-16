"""Handle reading logfiles and parsing them."""

import os
import sys
import re

from . import model


def calculate_game_gid(log):
    """Calculate GID for a game. Sequell compatible.

    XXX: should include server source.
    """
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
        src = os.path.basename(logfile.split('-', 1)[0])
        if os.stat(logfile).st_size == 0:
            continue
        sys.stdout.flush()
        lines = 0
        processed_lines = model.get_log_pos(logfile)
        print("Reading %s%s... " % (logfile,
                                    (" from line %s" % processed_lines) if
                                    processed_lines else ''),
              end='')
        for line in open(logfile).readlines():
            lines += 1
            if lines <= processed_lines:
                continue
            if not line:  # skip blank lines
                continue
            log = {}
            log['src'] = src
            for field in re.split(pat, line):
                if not field:  # skip blank fields
                    continue
                k, v = field.split('=', 1)
                if v.isdigit():
                    v = int(v)
                else:
                    v = v.replace("::", ":")  # Logfile escaping as per above
                log[k] = v
            gid = calculate_game_gid(log)
            model.add_game(gid, log)
        print("done (%s new lines)" % (lines - processed_lines))
        model.save_log_pos(logfile, lines)
