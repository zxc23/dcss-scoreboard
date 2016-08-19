#!/bin/bash

CPU_COUNT="1"
if which nproc >/dev/null &>/dev/null ; then
    CPU_COUNT=$(nproc)
elif [[ $(uname) = 'Darwin' ]] ; then
    CPU_COUNT=$(sysctl -n hw.ncpu)
fi

git ls-files '*.py' | xargs -t -n1 -P "$CPU_COUNT" yapf -d
