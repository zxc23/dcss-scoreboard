"""Handle reading logfiles and parsing them."""

import dcss_scoreboard.model as model
import os
import sys
import re

import sqlalchemy
engine = sqlalchemy.create_engine('sqlite:///scoredata.db', echo=False)


def sqlite_performance_over_safety(dbapi_con, con_record):
    """Significantly speeds up inserts but will break on crash."""
    dbapi_con.execute('PRAGMA journal_mode = MEMORY')
    dbapi_con.execute('PRAGMA synchronous = OFF')


sqlalchemy.event.listen(engine, 'connect', sqlite_performance_over_safety)

model.metadata.create_all(engine)

conn = engine.connect()


def add_game(gid, data):
    """Add a game to the database."""
    try:
        conn.execute(model.game.insert(), gid=gid, logfile=data)
    except sqlalchemy.exc.IntegrityError:
        print("Duplicate game, ignoring:", gid)


def get_log_pos(logfile):
    """Get the number of lines we've already processed."""
    pass
    # print(dir(model.log_progress.c))
    s = model.log_progress.select().where(model.log_progress.c.logfile ==
                                          logfile)
    row = conn.execute(s).fetchone()
    if row:
        return row.lines_parsed
    else:
        return 0


def save_log_pos(logfile, pos):
    """Save the number of lines we've processed."""
    # print("Saving log pos for", logfile, "as", pos)
    try:
        conn.execute(model.log_progress.insert(),
                     logfile=logfile,
                     lines_parsed=pos)
    except sqlalchemy.exc.IntegrityError:
        conn.execute(model.log_progress.update().where(
            model.log_progress.c.logfile == logfile).values(lines_parsed=pos))


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
        processed_lines = get_log_pos(logfile)
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
            add_game(gid, log)
        print("done (%s new lines)" % (lines - processed_lines))
        save_log_pos(logfile, lines)
