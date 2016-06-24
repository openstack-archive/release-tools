#!/bin/bash -e

if [ "$#" == "0" ] || [ "$1" == "help" ] || [ "$1" == "h" ]; then
    printf "USAGE: ./eol_branch.sh branch eol_tag project "
    printf "[project [project [...]]]\n"
    printf "Run from workspace containing recent checkouts of project with a "
    printf "remote 'gerrit'\n"
    # TODO(jhesketh): make remote configurable
    # TODO(jhesketh): make dry-run an argument
    # TODO(jhesketh): make verbose an argument
    # TODO(jhesketh): make EOL message configurable
    exit 0
fi

DRY=true
VERBOSE=true
REMOTE=gerrit

# First argument is the branch to delete
BRANCH=$1
shift

# Second argument is the tag to use before deletion
TAG=$1
shift

EOL_MESSAGE="This branch ($BRANCH) is at End Of Life"

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
