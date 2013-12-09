#!/bin/bash
#
# Script to cut milestone-proposed branches in one shot
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
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
    echo "Usage: $0 SHA milestone projectname"
    echo
    echo "Example: $0 HEAD havana-1 keystone"
    exit 2
fi

SHA=$1
MILESTONE=$2
PROJECT=$3

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
git review -s

if git show-ref --verify --quiet refs/heads/milestone-proposed; then
  echo "milestone-proposed branch already exists !"
  cd ../..
  rm -rf $MYTMPDIR
  exit 1
fi

title "Creating milestone-proposed at $SHA"
git branch milestone-proposed $SHA
REALSHA=`git show-ref -s milestone-proposed`
git push gerrit milestone-proposed

title "Cleaning up repository"
cd ../..
rm -rf $MYTMPDIR

title "Waiting for tarball from $REALSHA"
$TOOLSDIR/wait_for_tarball.py $REALSHA

title "Setting FixCommitted bugs to FixReleased"
$TOOLSDIR/process_bugs.py $PROJECT --settarget=$MILESTONE --fixrelease
