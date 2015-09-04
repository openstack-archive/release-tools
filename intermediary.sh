#!/bin/bash
#
# Script to publish an intermediary release in one shot
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

if [ $# -lt 3 ]; then
    echo "Usage: $0 version SHA project [deliverable]"
    echo
    echo "Example: $0 2.4.0 HEAD swift"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

VERSION=$1
SHA=$2
PROJECT=$3
DELIVERABLE=$4
LPROJECT="$PROJECT"

if [[ "$DELIVERABLE" != "" ]]; then
    echo "Extra element in $DELIVERABLE deliverable"
    echo "Skipping bugs updates and upload to $DELIVERABLE LP page"
    SKIPBUGS=1
    LPROJECT="$DELIVERABLE"
fi

title "Checking Launchpad milestone $VERSION exists for $LPROJECT"
$TOOLSDIR/ms2version.py --onlycheck $LPROJECT $VERSION

setup_temp_space intermediary-$PROJECT

title "Cloning repository for $PROJECT"
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
git review -s
TARGETSHA=`git log -1 $SHA --format='%H'`

title "Tagging $TARGETSHA as $VERSION"
TAGMSG="${PROJECT^} $VERSION"
git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
git push gerrit $VERSION
REALSHA=`git show-ref -s --tags "$VERSION"`

if [[ "$SKIPTARBALL" != "1" ]]; then
    title "Waiting for tarball from $REALSHA"
    $TOOLSDIR/wait_for_tarball.py $REALSHA
fi

if [[ "$SKIPBUGS" != "1" ]]; then
    title "Setting FixCommitted bugs to FixReleased"
    $TOOLSDIR/process_bugs.py $LPROJECT --settarget=$VERSION --fixrelease
    read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
fi

if [[ "$SKIPUPLOAD" != "1" ]]; then
    title "Uploading tarball to Launchpad"
    $TOOLSDIR/upload_release.py $LPROJECT $VERSION \
        --deliverable=$PROJECT
else
    title "Marking milestone as released in Launchpad"
    $TOOLSDIR/upload_release.py $LPROJECT $VERSION --deliverable=$PROJECT --nop
fi
