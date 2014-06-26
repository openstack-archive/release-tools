#!/bin/bash
#
# Script to cut proposed/foo pre-release branch at RC1
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

if [ $# -lt 3 ]; then
    echo "Usage: $0 SHA series projectname"
    echo
    echo "Example: $0 HEAD juno keystone"
    exit 2
fi

SHA=$1
SERIES=$2
PROJECT=$3
RC1MILESTONE="$2-rc1"

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

title "Checking that $RC1MILESTONE exists"
$TOOLSDIR/ms2version.py --onlycheck $PROJECT $RC1MILESTONE

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
LANG=C git review -s

if $(git branch -r | grep proposed > /dev/null); then
  echo "A *proposed* branch already exists !"
  cd ../..
  rm -rf $MYTMPDIR
  exit 1
fi

title "Creating proposed/$SERIES at $SHA"
git branch proposed/$SERIES $SHA
REALSHA=`git show-ref -s proposed/$SERIES`
git push gerrit proposed/$SERIES

title "Cleaning up repository"
cd ../..
rm -rf $MYTMPDIR

title "Waiting for tarball from $REALSHA"
$TOOLSDIR/wait_for_tarball.py $REALSHA

title "Setting FixCommitted bugs to FixReleased"
$TOOLSDIR/process_bugs.py $PROJECT --settarget=$RC1MILESTONE --fixrelease
