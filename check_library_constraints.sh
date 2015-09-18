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

setup_temp_space update-constraints-$PROJECT

title "Making a list of library repositories"
repos="$(list-repos --code-only --tag type:library --tag release:managed | grep -v openstack-dev/pbr)"

clone_repo openstack/requirements
constraints_file=$MYTMPDIR/openstack/requirements/upper-constraints.txt
blacklist_file=$MYTMPDIR/openstack/requirements/blacklist.txt

for repo in $repos; do
    clone_repo $repo
done

title "Comparing constraints"
for repo in $repos; do
    echo -n "$repo: "
    cd $MYTMPDIR/$repo

    # NOTE(dhellmann): Convert _ to - in the way safe_name() does to
    # find the matching constraint entry.
    name=$(python setup.py --name | sed 's/_/-/g')
    if [[ -z "$name" ]]; then
        echo "could not get name in $repo, skipping"
        continue
    fi
    if grep -q "$name" "$blacklist_file"; then
        echo "blacklisted, skipping"
        continue
    fi

    version=$(git describe --abbrev=0)
    expected="${name}===${version}"
    existing=$(grep $name $constraints_file)
    echo -n "$existing "
    if [[ "$expected" != "$existing" ]]; then
        echo "UPDATE $expected"
    else
        echo "OK"
    fi

done
