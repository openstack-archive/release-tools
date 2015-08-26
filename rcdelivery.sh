#!/bin/bash
#
# Script to publish RCs (and final release) from stable/foo in one shot
#
# Copyright 2011-2014 Thierry Carrez <thierry@openstack.org>
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

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 series rcX|final projectname [deliverable]"
    echo
    echo "Example: $0 liberty rc2 keystone"
    echo "Example: $0 liberty final neutron-fwaas neutron"
    exit 2
fi

SERIES=$1
RC=$2
PROJECT=$3
DELIVERABLE=$4
LPROJECT="$PROJECT"

if [[ "$PROJECT" == "oslo-incubator" ]]; then
    echo "Oslo-incubator mode: skipping tarball generation and upload"
    SKIPTARBALL=1
    SKIPUPLOAD=1
fi

if [[ "$DELIVERABLE" != "" ]]; then
    echo "Extra element in $DELIVERABLE deliverable"
    echo "Tarball will be uploaded to $DELIVERABLE LP page"
    LPROJECT="$DELIVERABLE"
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

title "Cloning repository for $PROJECT"
setup_temp_space rc-delivery-$PROJECT
clone_repo openstack/$PROJECT stable/$SERIES
cd openstack/$PROJECT

title "Resolving $LPROJECT $SERIES $RC to version"
FINALVERSION=`grep "^version = " setup.cfg | awk -F" " '{ print $3 }'`
if [[ "$FINALVERSION" == "" ]]; then
    echo "Could not determine pre-version from setup.cfg"
    exit 1
fi
if [[ "$RC" == "final" ]]; then
    MILESTONE=$FINALVERSION
    VERSION=$FINALVERSION
    $TOOLSDIR/ms2version.py --onlycheck $LPROJECT $MILESTONE
else
    MILESTONE="$SERIES-$RC"
    VERSION="${FINALVERSION}.0${RC}"
fi
echo "${PROJECT^} $SERIES $RC (milestone $MILESTONE) is version $VERSION"
if [[ "$VERSION" != "$FINALVERSION" ]]; then
    echo "Final $SERIES version will be $FINALVERSION"
fi

if [[ "$RC" == "final" ]]; then
    TAGMSG="${PROJECT^} $VERSION"
else
    TAGMSG="${PROJECT^} $MILESTONE milestone ($VERSION)"
fi
title "Tagging $VERSION ($TAGMSG)"
git tag -m "$TAGMSG" -s "$VERSION"
SHA=`git show-ref -s "$VERSION"`
git push gerrit $VERSION

if [[ "$SKIPTARBALL" != "1" ]]; then
    title "Waiting for tarball from $SHA"
    $TOOLSDIR/wait_for_tarball.py $SHA
fi

if [[ "$SKIPUPLOAD" != "1" ]]; then
    title "Uploading tarball to Launchpad"
    if [[ "$RC" == "final" ]]; then
        $TOOLSDIR/upload_release.py $LPROJECT $FINALVERSION \
        --deliverable=$PROJECT
    else
        $TOOLSDIR/upload_release.py $LPROJECT $FINALVERSION \
        --deliverable=$PROJECT --milestone=$MILESTONE
    fi
else
    title "Marking milestone as released in Launchpad"
    if [[ "$RC" == "final" ]]; then
        $TOOLSDIR/upload_release.py $LPROJECT $FINALVERSION \
        --deliverable=$PROJECT --nop
    else
        $TOOLSDIR/upload_release.py $LPROJECT $FINALVERSION \
        --deliverable=$PROJECT --milestone=$MILESTONE --nop
    fi
fi
