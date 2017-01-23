#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in all
# projects that have not yet been release.

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename $0) <releases-dir>"
    exit 1
fi

RELEASES_DIR=$1
list_deliverables=$RELEASES_DIR/.tox/venv/bin/list-deliverables

# Set up the virtualenv where the list-deliverables command will be
# found. This is done outside of the invocation below because
# otherwise we get the tox output mixed up in the repo list output and
# try to do things like look at the history of "venv" and
# "installing".
if [[ ! -d $RELEASES_DIR/.tox/venv ]]; then
    (cd $RELEASES_DIR && tox -e venv --notest)
fi
get_deliverable_owner=$RELEASES_DIR/.tox/venv/bin/get-deliverable-owner

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

if [[ -z "$VIRTUAL_ENV" ]]; then
    (cd $TOOLSDIR && tox -e venv --notest)
fi

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

echo "Finding deliverables with no releases in the current series..."
deliverables=$($list_deliverables --unreleased)
for deliv in $deliverables; do
    echo $deliv
done

function show_deliv () {
    # Show some details about the deliverable

    title $deliv
    echo
    $list_deliverables --deliverable "$deliv" -v

    # Show the changes for each repo for the deliverable, as defined
    # by the previous series releases.
    repos=$($list_deliverables --deliverable "$deliv" --repos --series "$previous_series")
    $TOOLSDIR/list_unreleased_changes.sh master $repos
}

for deliv in $deliverables; do

    owner=$($get_deliverable_owner $deliv | sed -e 's/ /-/g')
    if [[ -z "$owner" ]]; then
        echo "ERROR: No owner for $deliv"
        continue
    fi

    outfile=$TOOLSDIR/unreleased-${current_series}-${owner}.txt

    show_deliv $deliv 2>&1 | tee $outfile
done
