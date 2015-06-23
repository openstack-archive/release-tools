#!/bin/bash
#
# Script to publish a milestone in one shot
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

if [ $# -lt 3 ]; then
    echo "Usage: $0 milestone SHA project"
    echo
    echo "Example: $0 juno-1 HEAD keystone"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

MILESTONE=$1
SHA=$2
PROJECT=$3
LPROJECT="$PROJECT"

if [[ "$PROJECT" == "oslo-incubator" ]]; then
    echo "Oslo-incubator mode: skipping tarball generation and upload"
    SKIPTARBALL=1
    SKIPUPLOAD=1
fi

if [[ "$PROJECT" == neutron-* ]]; then
    echo "Neutron advanced services mode: skipping bugs and upload to neutron"
    SKIPBUGS=1
    LPROJECT="neutron"
fi

setup_temp_space milestone-$PROJECT

title "Cloning repository for $PROJECT"
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
git review -s
TARGETSHA=`git log -1 $SHA --format='%H'`

title "Resolving $MILESTONE to version"
RELVERSION=`grep "version = " setup.cfg | awk -F" " '{ print $3 }'`
if [[ "$RELVERSION" == "" ]]; then
    echo "Could not determine pre-version from setup.cfg"
    exit 1
fi
VERSION="${RELVERSION}.0b${MILESTONE: -1}"
echo "${PROJECT^} $MILESTONE is $VERSION (final being $RELVERSION)"

title "Tagging $TARGETSHA as $VERSION"
TAGMSG="${PROJECT^} $MILESTONE milestone ($VERSION)"
git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
git push gerrit $VERSION
REALSHA=`git show-ref -s --tags "$VERSION"`

if [[ "$SKIPTARBALL" != "1" ]]; then
    title "Waiting for tarball from $REALSHA"
    $TOOLSDIR/wait_for_tarball.py $REALSHA
fi

if [[ "$SKIPBUGS" != "1" ]]; then
    title "Setting FixCommitted bugs to FixReleased"
    $TOOLSDIR/process_bugs.py $LPROJECT --settarget=$MILESTONE --fixrelease
    read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
fi

if [[ "$SKIPUPLOAD" != "1" ]]; then
    title "Uploading tarball to Launchpad"
    $TOOLSDIR/upload_release.py $LPROJECT $RELVERSION \
        --deliverable=$PROJECT --milestone=$MILESTONE
else
    title "Marking milestone as released in Launchpad"
    $TOOLSDIR/upload_release.py $LPROJECT $RELVERSION --deliverable=$PROJECT \
        --milestone=$MILESTONE --nop
fi
