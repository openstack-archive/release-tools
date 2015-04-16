#!/bin/bash
#
# Update the .gitreview file in a specific branch of a checked out
# repository. Use oslo-incubator/tools/clone_openstack.sh to check out
# all of the projects under openstack/*
#
# Usage: $0 $branch <dir> [<dir>...]

NEW_BRANCH=$1
shift
dirs="$@"

set -x

function update_one () {
    grcontents="$(echo -n "$(cat .gitreview)")
defaultbranch=$NEW_BRANCH"
    echo "$grcontents" > .gitreview
    git add .gitreview
    git commit -m "update .gitreview for $NEW_BRANCH"
    git show
    git review
}

restore=$(pwd)

for d in $dirs
do
    # Reset the working directory, in case the logic below was
    # shortcut.
    cd $restore
    cd $d

    echo $d

    # Make sure the repository is current
    git checkout master
    git remote update

    # Only update the branch if the origin version exists
    if ! $(git branch -r | grep -q "origin/$NEW_BRANCH")
    then
        echo "No origin/$NEW_BRANCH for $(pwd)"
        continue
    fi

    # Create a local branch if none exists
    if ! $(git branch -r | grep -q " $NEW_BRANCH")
    then
        git branch $NEW_BRANCH origin/$NEW_BRANCH
    fi
    git checkout $NEW_BRANCH || continue

    if ! $(grep -q "defaultbranch =$NEW_BRANCH" .gitreview)
    then
        update_one
    fi
done
