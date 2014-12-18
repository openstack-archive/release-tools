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

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 series rcX|final projectname [swift_final_version]"
    echo
    echo "Example: $0 juno final keystone"
    echo "Example: $0 juno rc2 swift 2.1.0"
    exit 2
fi

SERIES=$1
RC=$2
PROJECT=$3

if [[ "$PROJECT" == "oslo-incubator" ]]; then
  echo "Oslo-incubator mode: skipping tarball generation and upload"
  SKIPTARBALL=1
  SKIPUPLOAD=1
fi

if [[ "$PROJECT" == "swift" ]]; then
  if [[ $# -eq 4 ]]; then
    FINALVERSION=$4
  else
    echo "Missing Swift final version number argument !"
    exit 2
  fi
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

title "Resolving $PROJECT $SERIES $RC to version"

if [[ "$RC" == "final" ]]; then
  if [[ "$PROJECT" != "swift" ]]; then
    RC1VERSION=`$TOOLSDIR/ms2version.py $PROJECT $SERIES-rc1`
    FINALVERSION=${RC1VERSION:0:8}
  fi
  MILESTONE=$FINALVERSION
  VERSION=$FINALVERSION
  $TOOLSDIR/ms2version.py --onlycheck $PROJECT $MILESTONE
else
  if [[ "$PROJECT" != "swift" ]]; then
    MILESTONE="$SERIES-$RC"
    VERSION=`$TOOLSDIR/ms2version.py $PROJECT $MILESTONE`
    FINALVERSION=${VERSION:0:8}
  else
    MILESTONE="$FINALVERSION-$RC"
    VERSION="${FINALVERSION}$RC"
    $TOOLSDIR/ms2version.py --onlycheck $PROJECT $MILESTONE
  fi
fi
echo "$SERIES $RC (milestone $MILESTONE) is version $VERSION"
echo "Final $SERIES version will be $FINALVERSION"

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT -b proposed/$SERIES
cd $PROJECT
LANG=C git review -s

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

  title "Checking tarball is similar to last proposed-$SERIES.tar.gz"
  $TOOLSDIR/similar_tarballs.sh $PROJECT proposed-$SERIES $VERSION
  read -sn 1 -p "Press any key to continue..."
fi

if [[ "$SKIPUPLOAD" != "1" ]]; then
  title "Uploading tarball to Launchpad"
  if [[ "$RC" == "final" ]]; then
    $TOOLSDIR/upload_release.py $PROJECT $FINALVERSION
  else
    $TOOLSDIR/upload_release.py $PROJECT $FINALVERSION --milestone=$MILESTONE
  fi
else
  title "Marking milestone as released in Launchpad"
  if [[ "$RC" == "final" ]]; then
    $TOOLSDIR/upload_release.py $PROJECT $FINALVERSION --nop
  else
    $TOOLSDIR/upload_release.py $PROJECT $FINALVERSION --milestone=$MILESTONE --nop
  fi
fi

title "Cleaning up"
cd ../..
rm -rf $MYTMPDIR
