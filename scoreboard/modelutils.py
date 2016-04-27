"""Utility functions for the model."""

import datetime


def crawl_date_to_datetime(d):
    """Converts a crawl date string to a datetime object.

    Note: crawl dates use a 0-indexed month... I think you can blame struct_tm
    for this.
    """
    # Increment the month by one
    d = d[:4] + '%02d' % (int(d[4:6]) + 1) + d[6:]
    return datetime.datetime(year=int(d[:4]),
                             month=int(d[4:6]),
                             day=int(d[6:8]),
                             hour=int(d[8:10]),
                             minute=int(d[10:12]),
                             second=int(d[12:14]))


def morgue_url(game):
    """Generates a morgue URL from a game."""
    if game.src == "cao":
        prefix = "http://crawl.akrasiac.org/rawdata"
    elif game.src == "cdo":
        prefix = "http://crawl.develz.org/morgues"
        prefix += "/" + version_url(game.v)
    elif game.src == "cszo":
        prefix = "http://dobrazupa.org/morgue"
    elif game.src == "cue" or game.src == "clan":
        prefix = "http://underhound.eu:81/crawl/morgue"
    elif game.src == "cbro":
        prefix = "http://crawl.berotato.org/crawl/morgue"
    elif game.src == "cxc":
        prefix = "http://crawl.xtahua.com/crawl/morgue"
    elif game.src == "lld":
        prefix = "http://lazy-life.ddo.jp:8080/morgue"
        prefix += "/" + version_url(game.v)
    elif game.src == "cpo":
        prefix = "https://crawl.project357.org/morgue"
    elif game.src == "cjr":
        prefix = "http://www.jorgrun.rocks/morgue"
    else:
        print("Failed", game)
        return None
    date = game.raw_data['end'][:4] \
    + "%02d" % (int(game.raw_data['end'][4:6]) + 1) \
    + game.raw_data['end'][6:8]
    time = game.raw_data['end'][8:14]
    result = "%s/%s/morgue-%s-%s-%s.txt" % (prefix, game.name, game.name, date, time)
    return result


def version_url(version):
    """Cleans up version strings for use in morgue URLs."""
    if version[-2:] == "a0":
        return "trunk"
    if len(version) > 4:
        for i in range(len(version)):
            if version[-(i+1)] == ".":
                return version[:-(i+1)]
    return version
