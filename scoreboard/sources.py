"""Parse Sequell's sources.yml file and download logfiles."""

import multiprocessing
import os
import subprocess
import urllib.parse
import re
from typing import Optional, Iterable, Sequence

import yaml
from braceexpand import braceexpand

import scoreboard.constants as const

SIMULTANEOUS_DOWNLOADS = 10
WGET_SOURCE_CMDLINE = ("wget --timeout 10 --no-verbose -c --tries 5 "
                       "-O '{outfile}' '{url}'")
# Ignored stuff: sprint & zotdef games, dead servers
IGNORED_FILES_REGEX = re.compile(
    r'(sprint|zotdef|rl.heh.fi|crawlus.somatika.net|nostalgia|mulch|squarelos|combo_god)')


def sources(src: dict) -> Iterable[str]:
    """Return a full, raw listing of logfile/milestone URLs for a given src dict.

    Expands bash style '{a,b}{1,2}' strings into all their permutations.
    Excludes URLs that match IGNORED_FILES_REGEX.
    """
    expanded_sources = []  # type: list
    if not src['base'].endswith('/'):
        src['base'] += '/'
    for line in src['logs']:
        # Some entries are dicts of the form { 'pattern': 'explbr'}
        # So when we want to support non-vanilla branches this will have to
        # be supported
        if not isinstance(line, str):
            continue
        # We don't support using autoindex folders to download wildcard file
        # names, luckily only a few weird files are affected so we just ignore
        # them until someone complains.
        line = line.replace('*', '')
        expanded_sources.extend(braceexpand(line))
    for line in expanded_sources:
        entry = "{}{}".format(src['base'], line)
        if re.search(IGNORED_FILES_REGEX, entry):
            continue
        if re.search(const.LOGFILE_REGEX, entry):
            yield entry


def source_data() -> dict:
    """Return a dict of {src: data, src: data} from source.yml."""
    out = {}
    rawpath = os.path.join(os.path.dirname(__file__), 'sources.yml')
    raw_yaml = yaml.load(open(rawpath, encoding='utf8'))
    for src in raw_yaml['sources']:
        out[src['name']] = tuple(sources(src))
    return out


def url_to_filename(url: str) -> str:
    """Convert milestone/logfile url to filename.

    Example:
        From: http://rl.heh.fi/meta/crawl-0.12/logfile
        To: meta-crawl-0.12-milestones.
    """
    return urllib.parse.urlparse(url).path.lstrip('/').replace('/', '-')


def download_source_files(urls: Sequence, dest: str) -> None:
    """Download logfile/milestone files for a single source."""
    print("Downloading {} files to {}".format(len(urls), dest))
    for url in urls:
        destfile = os.path.join(dest, url_to_filename(url))
        # Skip 0-byte files -- the source is assumed bad
        if os.path.exists(destfile) and os.stat(destfile).st_size == 0:
            continue
        # print("Downloading {} to {}".format(url, destfile))
        cmdline = WGET_SOURCE_CMDLINE.format(outfile=destfile, url=url)
        p = subprocess.run(cmdline,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        if p.returncode:
            print("Couldn't download {}. Error: {}".format(url, p.stderr))
            if b'ERROR 404' in p.stderr or b'ERROR 403' in p.stderr:
                # Write a zero-byte file so we don't try it again in future
                open(destfile, 'w').close()
        else:
            print("Finished downloading {}.".format(url))


def download_sources(dest: str, servers: Optional[str]=None) -> None:
    """Download all logfile/milestone files.

    Parameters:
        dest: path to download destination directory
        servers: if specified, the servers to download from

    Returns:
        Nothing
    """
    print("Downloading source files to {}".format(dest))
    if not os.path.exists(dest):
        os.mkdir(dest)
    all_sources = source_data()
    if servers:
        temp = {}
        for server in servers:
            if server in all_sources:
                temp[server] = all_sources[server]
                print("Downloading from whitelisted server '%s'." % server)
            else:
                print("Invalid server '%s' specified, skipping." % server)
        all_sources = temp
    # Not yet in typeshet
    p = multiprocessing.Pool(10)  # type: ignore
    jobs = []
    for src, urls in all_sources.items():
        destdir = os.path.join(dest, src)
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        jobs.append(p.apply_async(download_source_files, (urls, destdir)))
    for job in jobs:
        job.get()
    p.close()
    p.join()
