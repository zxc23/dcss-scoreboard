"""Handle reading logfiles and parsing them."""

import dcss_scoreboard.model as model
import os
import sys
import re

from sqlalchemy import create_engine
engine = create_engine('sqlite:///scoredata.db', echo=True)

model.metadata.create_all(engine)

conn = engine.connect()

def add_game(gid, data):
    conn.execute(model.game.insert(), gid=gid, logfile=data)

def calculate_game_gid(log):
    # XXX: should include server source
    return "%s:%s" % (log['name'], log['start'])

def load_logfiles():
    import glob
    pat = '(?<!:):(?!:)'  # logfile format escapes : as ::, so we need to split with re.split instead of naive line.split(':')
    for logfile in glob.glob("logfiles/*"):
        if os.stat(logfile).st_size == 0:
            continue
        print("Reading %s... " % logfile, end='')
        sys.stdout.flush()
        lines = 0
        for line in open(logfile).readlines():
            lines += 1
            if not line:  # skip blank lines
                continue
            log = {}
            for field in re.split(pat, line):
                if not field:  # skip blank fields
                    continue
                k, v = field.split('=', 1)
                if v.isdigit():
                    v = int(v)
                else:
                    v = v.replace("::", ":") # Logfile escaping as per above
                log[k] = v
            gid = calculate_game_gid(log)
            add_game(gid, log)
        print("done (%s lines)" % lines)
