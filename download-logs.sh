#!/bin/bash
set -eu

mkdir -p real-logfiles
cd real-logfiles

# CAO
wget -c -O cao-logfile-0.15 http://crawl.akrasiac.org/logfile15 &
wget -c -O cao-logfile-0.16 http://crawl.akrasiac.org/logfile16 &
wget -c -O cao-logfile-0.17 http://crawl.akrasiac.org/logfile17 &
wget -c -O cao-logfile-0.18 http://crawl.akrasiac.org/logfile18 &
wget -c -O cao-logfile-git http://crawl.akrasiac.org/logfile-git &

# CBRO
wget -c -O cbro-logfile-0.15 http://crawl.berotato.org/crawl/meta/0.15/logfile &
wget -c -O cbro-logfile-0.16 http://crawl.berotato.org/crawl/meta/0.16/logfile &
wget -c -O cbro-logfile-0.17 http://crawl.berotato.org/crawl/meta/0.17/logfile &
wget -c -O cbro-logfile-0.18 http://crawl.berotato.org/crawl/meta/0.18/logfile &
wget -c -O cbro-logfile-git http://crawl.berotato.org/crawl/meta/git/logfile &

# CDO
wget -c -O cdo-logfile-0.15 http://crawl.develz.org/allgames-0.15.txt &
wget -c -O cdo-logfile-0.16 http://crawl.develz.org/allgames-0.16.txt &
wget -c -O cdo-logfile-0.17 http://crawl.develz.org/allgames-0.17.txt &
wget -c -O cdo-logfile-0.18 http://crawl.develz.org/allgames-0.18.txt &
wget -c -O cdo-logfile-svn http://crawl.develz.org/allgames-svn.txt &

# CUE
wget -c -O cue-logfile-0.15 http://underhound.eu:81/crawl/meta/0.15/logfile &
wget -c -O cue-logfile-0.16 http://underhound.eu:81/crawl/meta/0.16/logfile &
wget -c -O cue-logfile-0.17 http://underhound.eu:81/crawl/meta/0.17/logfile &
wget -c -O cue-logfile-0.18 http://underhound.eu:81/crawl/meta/0.18/logfile &
wget -c -O cue-logfile-git http://underhound.eu:81/crawl/meta/git/logfile &

# CXC
wget -c -O cxc-logfile-0.15 http://crawl.xtahua.com/crawl/meta/0.15/logfile &
wget -c -O cxc-logfile-0.16 http://crawl.xtahua.com/crawl/meta/0.16/logfile &
wget -c -O cxc-logfile-0.17 http://crawl.xtahua.com/crawl/meta/0.17/logfile &
wget -c -O cxc-logfile-0.18 http://crawl.xtahua.com/crawl/meta/0.18/logfile &
wget -c -O cxc-logfile-git http://crawl.xtahua.com/crawl/meta/git/logfile &

# CWZ
wget -c -O cwz-logfile-0.15 http://webzook.net/soup/0.15/logfile &
wget -c -O cwz-logfile-0.16 http://webzook.net/soup/0.16/logfile &
wget -c -O cwz-logfile-0.17 http://webzook.net/soup/0.17/logfile &
wget -c -O cwz-logfile-0.18 http://webzook.net/soup/0.18/logfile &
wget -c -O cwz-logfile-git http://webzook.net/soup/trunk/logfile &

# LLD
wget -c -O lld-logfile-0.15 http://lazy-life.ddo.jp/mirror/meta/0.15/logfile &
wget -c -O lld-logfile-0.16 http://lazy-life.ddo.jp/mirror/meta/0.16/logfile &
wget -c -O lld-logfile-0.17 http://lazy-life.ddo.jp/mirror/meta/0.17/logfile &
wget -c -O lld-logfile-0.18 http://lazy-life.ddo.jp/mirror/meta/0.18/logfile &
wget -c -O lld-logfile-git http://lazy-life.ddo.jp/mirror/meta/trunk/logfile &

# CPO
wget -c -O cpo-logfile-0.15 https://crawl.project357.org/dcss-logfiles-0.15 &
wget -c -O cpo-logfile-0.16 https://crawl.project357.org/dcss-logfiles-0.16 &
wget -c -O cpo-logfile-0.17 https://crawl.project357.org/dcss-logfiles-0.17 &
wget -c -O cpo-logfile-0.18 https://crawl.project357.org/dcss-logfiles-0.18 &
wget -c -O cpo-logfile-trunk https://crawl.project357.org/dcss-logfiles-trunk &

