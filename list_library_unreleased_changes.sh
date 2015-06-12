#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in all
# libraries, so we don't have to remember the incantation.

if [[ $# -gt 1 ]]; then
    echo "Usage: $(basename $0) <branch>"
    exit 1
fi

SERIES=${1:-master}

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

if [[ -z "$VIRTUAL_ENV" ]]; then
    tox -e venv --notest
    source ./.tox/venv/bin/activate
fi

repos="$(list-repos --code-only --tag type:library --tag release:managed)"

$TOOLSDIR/list_unreleased_changes.sh $SERIES $repos
