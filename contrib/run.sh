#!/bin/bash

# This script runs the scoreboard in production
# Usage: run-one-constantly /scoreboard/run.sh

cd /scoreboard
. /root/venv/bin/activate
./loader.py --download-logfiles --urlbase 'https://scoreboard.crawl.develz.org' --extra-player-pages 50
echo
echo "Done"
echo
sleep 5
