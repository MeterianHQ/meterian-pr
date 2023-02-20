#!/bin/bash

if [[ "${1:-}" == "" ]]; then
    echo "Please provide a End2End test filename"
    exit -1
fi

github_path="tests/vcs/github/"
gitlab_path="tests/vcs/gitlab/"

if [[ -f "$github_path$1" ]]; then
    python3 -m "tests.vcs.github.${1:0:-3}"
    exit $?
fi

if [[ -f "$gitlab_path$1" ]]; then
    python3 -m "tests.vcs.github.${1:0:-3}"
    exit $?
fi

echo "Error: unknown test $1!"
