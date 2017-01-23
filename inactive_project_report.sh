#!/bin/bash
#
# Convenience wrapper to show details about projects that have not yet
# been releases.

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename $0) <releases-dir>"
    exit 1
fi

RELEASES_DIR=$(realpath $1)
list_deliverables=$RELEASES_DIR/.tox/venv/bin/list-deliverables

# Set up the virtualenv where the list-deliverables command will be
# found. This is done outside of the invocation below because
# otherwise we get the tox output mixed up in the repo list output and
# try to do things like look at the history of "venv" and
# "installing".
if [[ ! -d $RELEASES_DIR/.tox/venv ]]; then
    (cd $RELEASES_DIR && tox -e venv --notest)
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

if [[ -z "$VIRTUAL_ENV" ]]; then
    (cd $TOOLSDIR && tox -e venv --notest)
fi

setup_temp_space inactive-project-report

# Figure out the current series from the releases directory.
current_series=$($RELEASES_DIR/.tox/venv/bin/python -c 'import openstack_releases.defaults; print openstack_releases.defaults.RELEASE')
if [ -z "$current_series" ]; then
    echo "Could not determine the current release series."
    exit 1
fi

# Figure out the previous series from the releases directory.
previous_series=$(ls $RELEASES_DIR/deliverables | grep -B1 $current_series | head -n 1)
if [ -z "$previous_series" ]; then
    echo "Could not determine the previous release series."
    exit 1
fi

echo "Finding deliverables with no releases during ${current_series}..."
deliverables=$($list_deliverables --unreleased)

for deliv in $deliverables; do
    title $deliv

    # Show some details about the deliverable
    echo
    $list_deliverables --deliverable "$deliv" -v

    repos=$($list_deliverables --deliverable "$deliv" --repos --series "$previous_series")

    # We need the tools virtualenv to get zuul-cloner.
    source $TOOLSDIR/.tox/venv/bin/activate

    for repo in $repos; do
        title "$repo"
        echo
        clone_repo $repo
        cd $repo
        echo "Current version: $(git describe)"
        echo
        git log -n 1 --no-notes
        echo
        cd $MYTMPDIR
    done

    # We don't want to keep the tools virtualenv active because it
    # breaks list-deliverables.
    deactivate
done
