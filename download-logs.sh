#!/bin/bash

set -u

echo "Downloading logfiles to $(pwd)/real-logfiles..."

mkdir -p real-logfiles
cd real-logfiles

# CAO
wget -qc -O cao-logfile-0.15 http://crawl.akrasiac.org/logfile15
wget -qc -O cao-logfile-0.16 http://crawl.akrasiac.org/logfile16
wget -qc -O cao-logfile-0.17 http://crawl.akrasiac.org/logfile17
wget -qc -O cao-logfile-0.18 http://crawl.akrasiac.org/logfile18
wget -qc -O cao-logfile-git http://crawl.akrasiac.org/logfile-git

# CBRO
wget -qc -O cbro-logfile-0.15 http://crawl.berotato.org/crawl/meta/0.15/logfile
wget -qc -O cbro-logfile-0.16 http://crawl.berotato.org/crawl/meta/0.16/logfile
wget -qc -O cbro-logfile-0.17 http://crawl.berotato.org/crawl/meta/0.17/logfile
wget -qc -O cbro-logfile-0.18 http://crawl.berotato.org/crawl/meta/0.18/logfile
wget -qc -O cbro-logfile-git http://crawl.berotato.org/crawl/meta/git/logfile

# CDO
wget -qc -O cdo-logfile-0.15 http://crawl.develz.org/allgames-0.15.txt
wget -qc -O cdo-logfile-0.16 http://crawl.develz.org/allgames-0.16.txt
wget -qc -O cdo-logfile-0.17 http://crawl.develz.org/allgames-0.17.txt
wget -qc -O cdo-logfile-0.18 http://crawl.develz.org/allgames-0.18.txt
wget -qc -O cdo-logfile-svn http://crawl.develz.org/allgames-svn.txt

# CUE
wget -qc -O cue-logfile-0.15 http://underhound.eu:81/crawl/meta/0.15/logfile
wget -qc -O cue-logfile-0.16 http://underhound.eu:81/crawl/meta/0.16/logfile
wget -qc -O cue-logfile-0.17 http://underhound.eu:81/crawl/meta/0.17/logfile
wget -qc -O cue-logfile-0.18 http://underhound.eu:81/crawl/meta/0.18/logfile
wget -qc -O cue-logfile-git http://underhound.eu:81/crawl/meta/git/logfile

# CXC
wget -qc -O cxc-logfile-0.15 http://crawl.xtahua.com/crawl/meta/0.15/logfile
wget -qc -O cxc-logfile-0.16 http://crawl.xtahua.com/crawl/meta/0.16/logfile
wget -qc -O cxc-logfile-0.17 http://crawl.xtahua.com/crawl/meta/0.17/logfile
wget -qc -O cxc-logfile-0.18 http://crawl.xtahua.com/crawl/meta/0.18/logfile
wget -qc -O cxc-logfile-git http://crawl.xtahua.com/crawl/meta/git/logfile

# CWZ
wget -qc -O cwz-logfile-0.15 http://webzook.net/soup/0.15/logfile
wget -qc -O cwz-logfile-0.16 http://webzook.net/soup/0.16/logfile
wget -qc -O cwz-logfile-0.17 http://webzook.net/soup/0.17/logfile
wget -qc -O cwz-logfile-0.18 http://webzook.net/soup/0.18/logfile
wget -qc -O cwz-logfile-git http://webzook.net/soup/trunk/logfile

# LLD
wget -qc -O lld-logfile-0.15 http://lazy-life.ddo.jp/mirror/meta/0.15/logfile
wget -qc -O lld-logfile-0.16 http://lazy-life.ddo.jp/mirror/meta/0.16/logfile
wget -qc -O lld-logfile-0.17 http://lazy-life.ddo.jp/mirror/meta/0.17/logfile
wget -qc -O lld-logfile-0.18 http://lazy-life.ddo.jp/mirror/meta/0.18/logfile
wget -qc -O lld-logfile-git http://lazy-life.ddo.jp/mirror/meta/trunk/logfile

# CPO
wget -qc -O cpo-logfile-0.15 https://crawl.project357.org/dcss-logfiles-0.15
wget -qc -O cpo-logfile-0.16 https://crawl.project357.org/dcss-logfiles-0.16
wget -qc -O cpo-logfile-0.17 https://crawl.project357.org/dcss-logfiles-0.17
wget -qc -O cpo-logfile-0.18 https://crawl.project357.org/dcss-logfiles-0.18
wget -qc -O cpo-logfile-trunk https://crawl.project357.org/dcss-logfiles-trunk
