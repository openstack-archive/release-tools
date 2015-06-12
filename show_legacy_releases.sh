#!/bin/bash
#
# Scan the repositories for which we manage releases and show their
# existing date-based releases.

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

setup_temp_space generate-semver

REPOS="$($TOOLSDIR/list_repos_by_tag.py 'release:managed' | sort)"

for repo in $REPOS; do
    title "$repo"
    url=git://git.openstack.org/$repo
    git ls-remote --tags $url \
        | cut -f3- -d/ \
        | grep -v '{}' \
        | grep -v -- - \
        | cut -f1-2 -d. \
        | sort -u
    echo
done
