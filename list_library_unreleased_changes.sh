#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in all
# libraries, so we don't have to remember the incantation.

if [[ $# -ne 2 ]]; then
    echo "Usage: $(basename $0) <branch> <releases-dir>"
    exit 1
fi

SERIES=${1:-master}
RELEASES_DIR=$2

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

# Set up the virtualenv where the list-deliverables command will be
# found. This is done outside of the invocation below because
# otherwise we get the tox output mixed up in the repo list output and
# try to do things like look at the history of "venv" and
# "installing".
(cd $RELEASES_DIR && tox -e venv --notest)

echo "Finding $SERIES library repositories..."
repos="$($RELEASES_DIR/.tox/venv/bin/list-deliverables --repos --type library --series $SERIES)"

$TOOLSDIR/list_unreleased_changes.sh $SERIES $repos
