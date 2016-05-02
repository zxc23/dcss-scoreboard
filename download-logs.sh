#!/bin/bash

set -ue

WGET_OPTS="--no-verbose -c"

cd "$(dirname "$0")"
echo "Downloading logfiles to $(pwd)/real-logfiles..."

mkdir -p real-logfiles
cd real-logfiles

bash -c "
wget $WGET_OPTS -O cao-logfile-0.1-0.3 http://crawl.akrasiac.org/allgames.txt
wget $WGET_OPTS -O cao-logfile-0.4 http://crawl.akrasiac.org/logfile04
wget $WGET_OPTS -O cao-logfile-0.5 http://crawl.akrasiac.org/logfile05
wget $WGET_OPTS -O cao-logfile-0.6 http://crawl.akrasiac.org/logfile06
wget $WGET_OPTS -O cao-logfile-0.7 http://crawl.akrasiac.org/logfile07
wget $WGET_OPTS -O cao-logfile-0.8 http://crawl.akrasiac.org/logfile08
wget $WGET_OPTS -O cao-logfile-0.9 http://crawl.akrasiac.org/logfile09
wget $WGET_OPTS -O cao-logfile-0.10 http://crawl.akrasiac.org/logfile10
wget $WGET_OPTS -O cao-logfile-0.11 http://crawl.akrasiac.org/logfile11 ;
wget $WGET_OPTS -O cao-logfile-0.12 http://crawl.akrasiac.org/logfile12 ;
wget $WGET_OPTS -O cao-logfile-0.13 http://crawl.akrasiac.org/logfile13 ;
wget $WGET_OPTS -O cao-logfile-0.14 http://crawl.akrasiac.org/logfile14 ;
wget $WGET_OPTS -O cao-logfile-0.15 http://crawl.akrasiac.org/logfile15 ;
wget $WGET_OPTS -O cao-logfile-0.16 http://crawl.akrasiac.org/logfile16 ;
wget $WGET_OPTS -O cao-logfile-0.17 http://crawl.akrasiac.org/logfile17 ;
wget $WGET_OPTS -O cao-logfile-0.18 http://crawl.akrasiac.org/logfile18 ;
wget $WGET_OPTS -O cao-logfile-git http://crawl.akrasiac.org/logfile-git" &

bash -c "
wget $WGET_OPTS -O cdo-logfile-0.4 http://crawl.develz.org/allgames-0.4.txt ;
wget $WGET_OPTS -O cdo-logfile-0.5 http://crawl.develz.org/allgames-0.5.txt ;
wget $WGET_OPTS -O cdo-logfile-0.6 http://crawl.develz.org/allgames-0.6.txt ;
wget $WGET_OPTS -O cdo-logfile-0.7 http://crawl.develz.org/allgames-0.7.txt ;
wget $WGET_OPTS -O cdo-logfile-0.8 http://crawl.develz.org/allgames-0.8.txt ;
wget $WGET_OPTS -O cdo-logfile-0.10 http://crawl.develz.org/allgames-0.10.txt ;
wget $WGET_OPTS -O cdo-logfile-0.11 http://crawl.develz.org/allgames-0.11.txt ;
wget $WGET_OPTS -O cdo-logfile-0.12 http://crawl.develz.org/allgames-0.12.txt ;
wget $WGET_OPTS -O cdo-logfile-0.13 http://crawl.develz.org/allgames-0.13.txt ;
wget $WGET_OPTS -O cdo-logfile-0.14 http://crawl.develz.org/allgames-0.14.txt ;
wget $WGET_OPTS -O cdo-logfile-0.15 http://crawl.develz.org/allgames-0.15.txt ;
wget $WGET_OPTS -O cdo-logfile-0.16 http://crawl.develz.org/allgames-0.16.txt ;
wget $WGET_OPTS -O cdo-logfile-0.17 http://crawl.develz.org/allgames-0.17.txt ;
wget $WGET_OPTS -O cdo-logfile-0.18 http://crawl.develz.org/allgames-0.18.txt ;
wget $WGET_OPTS -O cdo-logfile-svn http://crawl.develz.org/allgames-svn.txt" &

bash -c "
wget $WGET_OPTS -O cszo-logfile-0.10 http://dobrazupa.org/meta/0.10/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.11 http://dobrazupa.org/meta/0.11/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.12 http://dobrazupa.org/meta/0.12/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.13 http://dobrazupa.org/meta/0.13/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.14 http://dobrazupa.org/meta/0.14/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.15 http://dobrazupa.org/meta/0.15/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.16 http://dobrazupa.org/meta/0.16/logfile ;
wget $WGET_OPTS -O cszo-logfile-0.17 http://dobrazupa.org/meta/0.17/logfile ;
wget $WGET_OPTS -O cszo-logfile-git http://dobrazupa.org/meta/git/logfile ;
" &

bash -c "
wget $WGET_OPTS -O cue-logfile-0.10 http://underhound.eu:81/crawl/meta/0.10/logfile ;
wget $WGET_OPTS -O cue-logfile-0.11 http://underhound.eu:81/crawl/meta/0.11/logfile ;
wget $WGET_OPTS -O cue-logfile-0.12 http://underhound.eu:81/crawl/meta/0.12/logfile ;
wget $WGET_OPTS -O cue-logfile-0.13 http://underhound.eu:81/crawl/meta/0.13/logfile ;
wget $WGET_OPTS -O cue-logfile-0.14 http://underhound.eu:81/crawl/meta/0.14/logfile ;
wget $WGET_OPTS -O cue-logfile-0.15 http://underhound.eu:81/crawl/meta/0.15/logfile ;
wget $WGET_OPTS -O cue-logfile-0.16 http://underhound.eu:81/crawl/meta/0.16/logfile ;
wget $WGET_OPTS -O cue-logfile-0.17 http://underhound.eu:81/crawl/meta/0.17/logfile ;
wget $WGET_OPTS -O cue-logfile-0.18 http://underhound.eu:81/crawl/meta/0.18/logfile ;
wget $WGET_OPTS -O cue-logfile-git http://underhound.eu:81/crawl/meta/git/logfile" &

# 0.13 - 0.16 logfiles no longer exist
bash -c "
wget $WGET_OPTS -O cwz-logfile-0.17 http://webzook.net/soup/0.17/logfile ;
wget $WGET_OPTS -O cwz-logfile-0.18 http://webzook.net/soup/0.18/logfile ;
wget $WGET_OPTS -O cwz-logfile-git http://webzook.net/soup/trunk/logfile" &

bash -c "
wget $WGET_OPTS -O cbro-logfile-0.13 http://crawl.berotato.org/crawl/meta/0.13/logfile ;
wget $WGET_OPTS -O cbro-logfile-0.14 http://crawl.berotato.org/crawl/meta/0.14/logfile ;
wget $WGET_OPTS -O cbro-logfile-0.15 http://crawl.berotato.org/crawl/meta/0.15/logfile ;
wget $WGET_OPTS -O cbro-logfile-0.16 http://crawl.berotato.org/crawl/meta/0.16/logfile ;
wget $WGET_OPTS -O cbro-logfile-0.17 http://crawl.berotato.org/crawl/meta/0.17/logfile ;
wget $WGET_OPTS -O cbro-logfile-0.18 http://crawl.berotato.org/crawl/meta/0.18/logfile ;
wget $WGET_OPTS -O cbro-logfile-git http://crawl.berotato.org/crawl/meta/git/logfile" &

bash -c "
wget $WGET_OPTS -O cxc-logfile-0.14 http://crawl.xtahua.com/crawl/meta/0.14/logfile ;
wget $WGET_OPTS -O cxc-logfile-0.15 http://crawl.xtahua.com/crawl/meta/0.15/logfile ;
wget $WGET_OPTS -O cxc-logfile-0.16 http://crawl.xtahua.com/crawl/meta/0.16/logfile ;
wget $WGET_OPTS -O cxc-logfile-0.17 http://crawl.xtahua.com/crawl/meta/0.17/logfile ;
wget $WGET_OPTS -O cxc-logfile-0.18 http://crawl.xtahua.com/crawl/meta/0.18/logfile ;
wget $WGET_OPTS -O cxc-logfile-git http://crawl.xtahua.com/crawl/meta/git/logfile" &

bash -c "
wget $WGET_OPTS -O lld-logfile-0.14 http://lazy-life.ddo.jp/mirror/meta/0.14/logfile ;
wget $WGET_OPTS -O lld-logfile-0.15 http://lazy-life.ddo.jp/mirror/meta/0.15/logfile ;
wget $WGET_OPTS -O lld-logfile-0.16 http://lazy-life.ddo.jp/mirror/meta/0.16/logfile ;
wget $WGET_OPTS -O lld-logfile-0.17 http://lazy-life.ddo.jp/mirror/meta/0.17/logfile ;
wget $WGET_OPTS -O lld-logfile-0.18 http://lazy-life.ddo.jp/mirror/meta/0.18/logfile ;
wget $WGET_OPTS -O lld-logfile-git http://lazy-life.ddo.jp/mirror/meta/trunk/logfile" &

bash -c "
wget $WGET_OPTS -O cpo-logfile-0.15 https://crawl.project357.org/dcss-logfiles-0.15 ;
wget $WGET_OPTS -O cpo-logfile-0.16 https://crawl.project357.org/dcss-logfiles-0.16 ;
wget $WGET_OPTS -O cpo-logfile-0.17 https://crawl.project357.org/dcss-logfiles-0.17 ;
wget $WGET_OPTS -O cpo-logfile-0.18 https://crawl.project357.org/dcss-logfiles-0.18 ;
wget $WGET_OPTS -O cpo-logfile-trunk https://crawl.project357.org/dcss-logfiles-trunk" &

bash -c "
wget $WGET_OPTS -O cjr-logfile-0.17 http://www.jorgrun.rocks/meta/0.17/logfile ;
wget $WGET_OPTS -O cjr-logfile-0.18 http://www.jorgrun.rocks/meta/0.18/logfile ;
wget $WGET_OPTS -O cjr-logfile-git http://www.jorgrun.rocks/meta/git/logfile ;
"

wait
