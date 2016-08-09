#!/bin/bash

git ls-files '*.py' | xargs -t -n1 yapf -d
