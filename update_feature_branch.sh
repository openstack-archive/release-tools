#!/bin/bash
set -e

# require a feature branch to be specified
if [ "$1" = "" ]
then
  echo "Usage: $0 <branchname>" >&2
  exit 1
fi
BRANCH=$1

# ensure the remote branch exists and is tracked
git branch --list | grep $BRANCH || git checkout --track origin/$BRANCH

# ensure master is up to date
git remote update

# ensure the feature branch is up to date
git reset --hard origin/$BRANCH

{
    # create a temporary branch
    git checkout -b merge-branch && \

    # create a merge commit
    git merge origin/master --message "Update the $BRANCH branch" && \

    # amend the merge commit to automatically add a Change-ID to the commit message
    GIT_EDITOR=true git commit --amend && \

    # push the merge commit to gerrit without a scary confirmation
    # git review --yes --no-rebase $BRANCH
    echo "git review --yes --no-rebase $BRANCH"
} || {
    echo "Failed to create and upload the merge commit." >&2
}

# switch off the branch so we can delete it
git checkout master~0

# delete the temporary branch
git branch -D merge-branch
