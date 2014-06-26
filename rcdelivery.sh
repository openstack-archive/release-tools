#!/bin/bash
#
# Script to publish RCs (and final release) from proposed/foo in one shot
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
    echo "Usage: $0 series rcX|final projectname"
    echo
    echo "Example: $0 juno rc1 keystone"
    exit 2
fi

SERIES=$1
RC=$2
PROJECT=$3

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

title "Resolving $SERIES $RC to version"

if [ "$RC" == "final" ]; then
  #TODO: Improve ms2version.py so that it can resolve "juno" directly
  #TODO: Check that final milestone actually exists (we only check rc1)
  RC1VERSION=`$TOOLSDIR/ms2version.py $PROJECT $SERIES-rc1`
  RELVERSION=${RC1VERSION:0:6}
  MILESTONE=$RELVERSION
  VERSION=$RELVERSION
else
  MILESTONE="$SERIES-$RC"
  VERSION=`$TOOLSDIR/ms2version.py $PROJECT $MILESTONE`
  RELVERSION=${VERSION:0:6}
fi
echo "$SERIES $RC ($MILESTONE) is $VERSION (final being $RELVERSION)"

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT -b proposed/$SERIES
cd $PROJECT
git review -s

if [ "$RELVERSION" == "$VERSION" ]; then
  TAGMSG="${PROJECT^} $VERSION"
else
  TAGMSG="${PROJECT^} $MILESTONE milestone ($VERSION)"
fi
title "Tagging $VERSION ($TAGMSG)"
git tag -m "$TAGMSG" -s "$VERSION"
SHA=`git show-ref -s "$VERSION"`
git push gerrit $VERSION

title "Waiting for tarball from $SHA"
$TOOLSDIR/wait_for_tarball.py $SHA

title "Checking tarball is similar to last milestone-proposed.tar.gz"
$TOOLSDIR/similar_tarballs.sh $PROJECT milestone-proposed $VERSION
read -sn 1 -p "Press any key to continue..."

title "Uploading tarball to Launchpad"
if [ "$RELVERSION" == "$VERSION" ]; then
  $TOOLSDIR/upload_release.py $PROJECT $VERSION
else
  $TOOLSDIR/upload_release.py $PROJECT $VERSION --milestone=$MILESTONE
fi

#TODO: If final, rename proposed/* to stable/* (if doable through API)

title "Cleaning up"
cd ../..
rm -rf $MYTMPDIR
