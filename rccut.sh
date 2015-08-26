#!/bin/bash
#
# Script to cut stable/foo pre-release branch at RC1
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
    echo "Usage: $0 SHA series projectname"
    echo
    echo "Example: $0 HEAD juno keystone"
    exit 2
fi

SHA=$1
SERIES=$2
PROJECT=$3
LPROJECT="$PROJECT"

if [[ "$PROJECT" == "oslo-incubator" ]]; then
    echo "Oslo-incubator mode: skipping tarball check"
    SKIPTARBALL=1
fi

if [[ "$PROJECT" == neutron-* ]]; then
    echo "Neutron advanced services mode: skipping bugs"
    SKIPBUGS=1
    LPROJECT="neutron"
fi

RC1MILESTONE="$SERIES-rc1"

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

title "Checking that $RC1MILESTONE exists"
$TOOLSDIR/ms2version.py --onlycheck $LPROJECT $RC1MILESTONE

title "Cloning repository for $PROJECT"
setup_temp_space rc-branch-$PROJECT
clone_repo openstack/$PROJECT
cd openstack/$PROJECT

if $(git branch -r | grep stable/$SERIES > /dev/null); then
    echo "The stable/$SERIES branch already exists !"
    exit 1
fi

title "Creating stable/$SERIES at $SHA"
git branch stable/$SERIES $SHA
REALSHA=`git show-ref -s stable/$SERIES`
git push gerrit stable/$SERIES

# No longer check tarballs since they can lag hours now
#if [[ "$SKIPTARBALL" != "1" ]]; then
#    title "Waiting for tarball from $REALSHA"
#    $TOOLSDIR/wait_for_tarball.py $REALSHA
#fi

if [[ "$SKIPBUGS" != "1" ]]; then
    title "Setting FixCommitted bugs to FixReleased"
    $TOOLSDIR/process_bugs.py $LPROJECT --settarget=$RC1MILESTONE --fixrelease
fi
