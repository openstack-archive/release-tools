#!/bin/bash
#
# Check the constraints settings for OpenStack libraries against their
# most current version.

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

if [[ -z "$VIRTUAL_ENV" ]]; then
    tox -e venv --notest
    source ./.tox/venv/bin/activate
fi

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <requirements-repo-dir>"
    exit 1
fi
REQ_REPO="$1"

setup_temp_space update-constraints-$PROJECT

title "Making a list of library repositories"
repos="$(list-repos --code-only --tag type:library --tag release:managed)"

constraints_file=$REQ_REPO/upper-constraints.txt
blacklist_file=$REQ_REPO/blacklist.txt

for repo in $repos; do
    clone_repo $repo
done

title "Comparing constraints"
for repo in $repos; do
    cd $MYTMPDIR/$repo

    # NOTE(dhellmann): Convert _ to - in the way safe_name() does to
    # find the matching constraint entry.
    name=$(python setup.py --name | sed 's/_/-/g')
    if [[ -z "$name" ]]; then
        echo "$repo: could not get name, skipping"
        continue
    fi
    if grep -q "^${name}=" "$blacklist_file"; then
        echo "$repo: blacklisted, skipping"
        continue
    fi

    version=$(git describe --abbrev=0)
    expected="${name}===${version}"
    existing=$(grep $name $constraints_file)
    if [[ "$expected" != "$existing" ]]; then
        echo "$existing UPDATE ${version}"
    fi

done
