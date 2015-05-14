#!/bin/bash
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Provide a list of the unreleased changes in the given repositories

bindir=$(cd $(dirname $0) && pwd)
branch="$1"
shift
repos="$@"

source $bindir/functions

# Make sure no pager is configured so the output is not blocked
export PAGER=

function get_last_tag {
    # Use git log to show changes on this branch, and add --decorate
    # to include the tag names. Then use grep and sed to pull the tag
    # name out so that is all we pass to highest_semver.py.
    #
    # This assumes the local copy of the repo is on the branch from
    # which we would want to release.
    git log --decorate --oneline \
        | egrep '^[0-9a-f]+ \((HEAD, )?tag: ' \
        | sed -r 's/^.+tag: ([^ ]+)[,\)].+$/\1/g' \
        | ${bindir}/highest_semver.py

    # Look at *all* tags, sorted by the date they were applied. This
    # sometimes predicts the wrong value, especially when we might be
    # releasing from a branch other than master.
    #
    # git for-each-ref --sort=taggerdate --format '%(refname)' refs/tags \
    #     | sed -e 's|refs/tags/||' \
    #     | ${bindir}/highest_semver.py
}

setup_temp_space 'list-unreleased'

function list_changes {
    git clone -q git://git.openstack.org/$repo -b $branch
    if [[ $? -ne 0 ]]; then
        return 1
    fi
    cd $(basename $repo)
    prev_tag=$(get_last_tag)
    if [ -z "$prev_tag" ]; then
        echo "$repo has not yet been released"
    else
        echo
        $bindir/release_notes.py \
            --show-dates \
            --changes-only \
            . $prev_tag HEAD
    fi
}

# Show the unreleased changes for each repository.
for repo in $repos; do
    cd $MYTMPDIR
    echo
    title "$repo"
    list_changes "$repo"
done
