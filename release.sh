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

if [ $# -lt 4 ]; then
    echo "Usage: $0 repository series version SHA"
    echo
    echo "Example: $0 openstack/oslo.rootwrap mitaka 3.0.3 gerrit/master"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

REPO=$1
SERIES=$2
VERSION=$3
SHA=$4
SHORTNAME=`basename $REPO`

if [[ -z "$VIRTUAL_ENV" ]]; then
    tox -e venv --notest
    source ./.tox/venv/bin/activate
fi

setup_temp_space release-tag-$SHORTNAME
clone_repo $REPO
REPODIR="$(cd $REPO && pwd)"
cd $REPODIR
TARGETSHA=`git log -1 $SHA --format='%H'`

title "Tagging $TARGETSHA as $VERSION"
if git show-ref "$VERSION"; then
    echo "$REPO already has a version $VERSION tag"
else
    TAGMSG="$SHORTNAME $VERSION release"
    echo "Tag message is '$TAGMSG'"
    git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
    git push gerrit $VERSION
fi

title "Adding comments to fixed bugs"
PREV_SERIES=""
if git branch -a | grep -q origin/stable/$SERIES; then
    PREV_SERIES=origin/stable/$SERIES
fi
PREVIOUS=$(get_last_tag $PREV_SERIES)
BUGS=$(git log $PREVIOUS..$VERSION | grep "Closes-Bug:" | egrep -o "[0-9]+")
$TOOLSDIR/add_comment.py \
    --subject="Fix included in $REPO $VERSION" \
    --content="This issue was fixed in $REPO $VERSION release." \
    $BUGS
