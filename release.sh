#!/bin/bash
#
# Script to release a project in one shot, including the git tag and
# launchpad updates.
#
# Copyright 2015 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
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

set -e

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

function usage {
    echo "Usage: release.sh [-a] repository series version SHA announce"
    echo
    echo "Example: release.sh openstack/oslo.rootwrap mitaka 3.0.3 gerrit/master openstack-dev@lists.openstack.org"
}

announce=false
while getopts "a" opt "$@"; do
    case "$opt" in
        a) announce=true;;
        ?) echo "Invalid option: -$OPTARG" >&2;
            usage;
            exit 1;;
    esac
done
shift $((OPTIND-1))

if [ $# -lt 5 ]; then
    usage
    exit 2
fi

REPO=$1
SERIES=$2
VERSION=$3
SHA=$4
ANNOUNCE=$5

SHORTNAME=`basename $REPO`

RELEASETYPE="release"
if [[ $VERSION =~ .*\.0[b,r].+ ]]; then
    RELEASETYPE="development milestone"
fi

setup_temp_space release-tag-$SHORTNAME
clone_repo $REPO
REPODIR="$(cd $REPO && pwd)"
cd $REPODIR
TARGETSHA=`git log -1 $SHA --format='%H'`

# Determine the most recent tag before we add the new one.
PREV_SERIES=""
if git branch -a | grep -q origin/stable/$SERIES; then
    PREV_SERIES=origin/stable/$SERIES
fi
PREVIOUS=$(get_last_tag $PREV_SERIES)

title "Tagging $TARGETSHA as $VERSION"
if git show-ref "$VERSION"; then
    echo "$REPO already has a version $VERSION tag"
    PREVIOUS=$(git describe --abbrev=0 ${VERSION}^1)
else
    # WARNING(dhellmann): announce.sh expects to be able to parse this
    # commit message, so if you change the format you may have to
    # update announce.sh as well.
    TAGMSG="$SHORTNAME $VERSION $RELEASETYPE

meta:version: $VERSION
meta:series: $SERIES
meta:release-type: $RELEASETYPE
meta:announce: $ANNOUNCE
"
    echo "Tag message is '$TAGMSG'"
    git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
    git push gerrit $VERSION
fi

# We don't want to die just because we can't update some bug reports,
# so ignore failures.
set +e

title "Adding comments to fixed bugs"
BUGS=$(git log $PREVIOUS..$VERSION | grep "Closes-Bug:" | egrep -o "[0-9]+")
if [[ -z "$BUGS" ]]; then
    echo "No bugs found $PREVIOUS .. $VERSION"
else
    $TOOLSDIR/launchpad_add_comment.py \
        --subject="Fix included in $REPO $VERSION" \
        --content="This issue was fixed in the $REPO $VERSION $RELEASETYPE." \
        $BUGS
fi

# If we're running the script by hand, we might want to generate a
# release announcement.
if $announce; then
    title "Generating release announcement"
    (cd $TOOLSDIR && ./announce.sh $REPODIR $VERSION)
fi

exit 0
