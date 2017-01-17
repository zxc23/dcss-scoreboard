#!/bin/bash

# This script runs the scoreboard in production
# Usage: run-one-constantly /app/scoreboard/run.sh

cd /app/scoreboard
. /root/venv/bin/activate
./loader.py --urlbase 'https://scoreboard.crawl.develz.org' --extra-player-pages 50 && ./update-dms.sh
