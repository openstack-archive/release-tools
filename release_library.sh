#!/bin/bash
#
# Script to release a library in one shot, including the git tag and
# launchpad updates.
#
# This script assumes that the library release manager follows pbr's
# SemVer rules for library versioning and has a launchpad project
# configured with a "next-$version" milestone (where $version is juno,
# kilo, etc.).
#
# Copyright 2014 Thierry Carrez <thierry@openstack.org>
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
    echo "Usage: $0 series version SHA launchpad-project"
    echo
    echo "Example: $0 juno 1.0.0 HEAD oslo.rootwrap"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

SERIES=$1
VERSION=$2
TARGET=$VERSION
SHA=$3
PROJECT=$4

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ $VERSION == *a* ]]; then
    ALPHA_RELEASE=1
    TARGET="next-$SERIES"
fi

setup_temp_space release-tag-$PROJECT

REPO=$(lp_project_to_repo $PROJECT)

title "Cloning repository for $PROJECT"
git clone git://git.openstack.org/openstack/$REPO
cd $REPO
git review -s

title "Sanity checking $VERSION"
if ! $TOOLSDIR/sanity_check_version.py $VERSION $(git tag)
then
    read -s -p "Press Ctrl-C to cancel or Return to continue..."
fi
TARGETSHA=`git log -1 $SHA --format='%H'`

title "Tagging $TARGETSHA as $VERSION"
if [[ "$ALPHA_RELEASE" != "1" ]]; then
    TAGMSG="$PROJECT $VERSION release"
else
    TAGMSG="$PROJECT $VERSION alpha milestone"
fi

if git branch -a | grep -q origin/stable/$SERIES; then
    STABLE_BRANCH=1
else
    STABLE_BRANCH=0
fi

if git show-ref "$VERSION"
then
    echo "$PROJECT already has a version $VERSION tag"
else
    if [[ "$STABLE_BRANCH" != "0" ]]; then
        prev_series=origin/stable/$SERIES
    else
        prev_series=""
    fi
    previous_rev=$(get_last_tag $prev_series)
    echo "Tag message is '$TAGMSG'"
    git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
    git push gerrit $VERSION
    title "Release notes"
    ${TOOLSDIR}/release_notes.py . $previous_rev $VERSION
fi

if [[ "$ALPHA_RELEASE" != "1" ]]; then
    title "Renaming next-$SERIES to $VERSION"
    $TOOLSDIR/rename_milestone.py $PROJECT next-$SERIES $VERSION
    echo "Do not forget to create a new next-$SERIES milestone"
fi

title "Setting FixCommitted bugs to FixReleased"
if [[ "$STABLE_BRANCH" != "1" ]]; then
    $TOOLSDIR/process_bugs.py $PROJECT --settarget=$TARGET --fixrelease
    read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
    echo
else
    read -sn 1 -p "Make sure all closed bugs are properly targeted, then press key to continue..."
    echo
fi

if [[ "$ALPHA_RELEASE" != "1" ]]; then
    title "Marking milestone as released in Launchpad"
    $TOOLSDIR/upload_release.py $PROJECT $VERSION --milestone=$TARGET --nop
fi
