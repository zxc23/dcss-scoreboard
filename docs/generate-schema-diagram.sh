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
./schemacrawler.sh -server=mysql -command=graph -infolevel=standard -user=test -password=test -host=localhost -database=dcss_scoreboard -outputformat png -outputfile="$origdir/uml.png" -schemas 'dcss_scoreboard.*'
