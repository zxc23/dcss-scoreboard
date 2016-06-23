#!/bin/bash

# Uses http://sualeh.github.io/SchemaCrawler/
# You may have to update user/password/host/database

set -eu

if [[ $# -ne 1 || -z "$1" ]] ; then
    echo "usage: $0 path/to/schemacrawler.sh"
    exit 1
fi
dir="$(dirname "$1")"

# Crazy logic to get the script's dir
pushd "$(dirname "$0")" > /dev/null
origdir=$(pwd)
popd > /dev/null

set -x
cd "$dir"
./schemacrawler.sh -command=graph -server=postgresql -user=scoreboard -password=scoreboard -host=localhost -database=scoreboard -outputformat png -infolevel=standard -outputfile="$origdir/uml.png"
