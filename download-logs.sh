#!/bin/bash
set -eu
#wget -O logfiles/cdo-logfile-0.17.txt http://crawl.develz.org/milestones-0.17.txt
cd logfiles
wget -c -O cao-logfile-0.17 http://crawl.akrasiac.org/logfile17 &
wget -c -O cao-logfile-git http://crawl.akrasiac.org/logfile-git &
wget -c -O cue-logfile-0.17 http://underhound.eu:81/crawl/meta/0.17/logfile &
wget -c -O cue-logfile-git http://underhound.eu:81/crawl/meta/git/logfile &
wget -c -O cbro-logfile-0.17 http://crawl.berotato.org/crawl/meta/0.17/logfile &
wget -c -O cbro-logfile-git http://crawl.berotato.org/crawl/meta/git/logfile &
wget -c -O cxc-logfile-0.17 http://crawl.xtahua.com/crawl/meta/0.17/logfile &
wget -c -O cxc-logfile-git http://crawl.xtahua.com/crawl/meta/git/logfile &
wget -c -O cpo-logfile-0.17 https://crawl.project357.org/dcss-logfiles-trunk  &
wget -c -O cpo-logfile-git https://crawl.project357.org/dcss-logfiles-0.17 &

