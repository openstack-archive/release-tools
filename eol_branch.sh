#!/bin/bash

function print_help {
    echo ""
    echo "USAGE:"
    echo " ./eol_branch.sh [options] branch eol_tag project [project [project [...]]]"
    echo ""
    echo "A tool for retiring old branches. Performs the following:"
    echo "1) Abandon stale reviews,"
    echo "2) tag current position of branch"
    echo "3) delete the branch from the remote"
    echo ""
    echo "Must be ran from a directory containing a recent checkout of the project[s]"
    echo ""
    echo "Options:"
    echo " --eol-message <message> Set the message on the end-of-life tag"
    echo " -d, --dry-run           Do not run any harmful commands"
    echo " -h, --help              This help message"
    echo " -q, --quiet             Turn off unimportant messages"
    echo " --remote <remote>       Set the remote to delete branches from (default: gerrit)"
    echo ""
}

OPTS=`getopt -o dhq --long eol-message:,dry,help,quiet,remote: -n $0 -- "$@"`
if [ $? != 0 ] ; then
    echo "Failed parsing options." >&2
    print_help
    exit 1
fi
eval set -- "$OPTS"
set -e
# Defaults:
EOL_MESSAGE=""
DRY=true
REMOTE=gerrit
VERBOSE=true

while true; do
    case "$1" in
        --eol-message)
            EOL_MESSAGE=$2
            shift
            shift
            ;;
        -d|--dry-run)
            VERBOSE=false
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        -q|--quiet)
            VERBOSE=false
            shift
            ;;
        --remote)
            REMOTE=$2
            shift
            shift
            ;;
        --)
            shift
            break
            ;;
    esac
done

# First argument is the branch to delete
BRANCH=$1
shift

# Second argument is the tag to use before deletion
TAG=$1
shift

if [$EOL_MESSAGE = ""]; then
    EOL_MESSAGE="This branch ($BRANCH) is at End Of Life"
fi


function abandon_reviews {
    project=$1
    if [ $VERBOSE = true ]; then
        echo "Running query: status:open project:$project branch:$BRANCH"
    fi

    gerrit_query="--current-patch-set status:open project:$project branch:$BRANCH"
    ssh -p 29418 review.openstack.org gerrit query $gerrit_query |
        grep revision | while read -r line; do
        rev=`echo $line | cut -b 11-`
        if [ $VERBOSE = true ]; then
            echo "Found commit $rev to abandon"
        fi
        if [ $DRY = true ]; then
            echo "ssh -p 29418 review.openstack.org gerrit review --project $project --abandon --message '\"$EOL_MESSAGE\"' $rev"
        else
            ssh -p 29418 review.openstack.org gerrit review --project $project --abandon --message '"$EOL_MESSAGE"' $rev
        fi
    done
}

function tag_eol {
    project=$1
    rev=`git rev-parse remotes/$REMOTE/$BRANCH`

    if git rev-parse $TAG >/dev/null 2>&1; then
        echo "WARN: The tag ($TAG) already exists on $project"
        tag_rev=`git rev-list -n 1 $TAG`
        if [ $rev != $tag_rev ]; then
            echo "ERROR: The tag ($tag_rev) doesn't match the branch ($rev)"
            exit 1
        fi
        return 0
    fi

    if [ $VERBOSE = true ]; then
        echo "About to add tag $TAG to $project at branch $BRANCH (rev $rev)"
    fi
    if [ $DRY = true ]; then
        echo "git tag -s $TAG -m \"$EOL_MESSAGE\" remotes/$REMOTE/$BRANCH"
        echo "git push gerrit $TAG"
    else
        git tag -s $TAG -m "$EOL_MESSAGE" remotes/$REMOTE/$BRANCH
        git push gerrit $TAG
    fi
}

function delete_branch {
    rev=`git rev-parse remotes/$REMOTE/$BRANCH`
    if [ $VERBOSE = true ]; then
        echo "About to delete the branch $BRANCH from $project (rev $rev)"
    fi
    if [ $DRY = true ]; then
        echo "git push $REMOTE --delete $BRANCH"
    else
        git push $REMOTE --delete $BRANCH
    fi
}


while (( "$#" )); do
    project=$1
    shift

    if ! [ -d $project/.git ]; then
        echo "$project is not a git repo"
        echo "skipping..."
        continue
    fi

    pushd $project
    git remote update --prune

    if ! git rev-parse remotes/$REMOTE/$BRANCH >/dev/null 2>&1; then
        echo "$project does not have a branch $BRANCH"
        echo "skipping..."
        popd
        continue
    fi

    abandon_reviews $project
    tag_eol $project
    delete_branch $project

    popd
done
