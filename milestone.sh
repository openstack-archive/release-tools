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

MILESTONE=$1
SHA=$2
PROJECT=$3

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

if [[ "$PROJECT" == "swift" ]]; then
  echo "Swift mode: skipping fixreleasing (bugs should be set at RC time)"
  SKIPBUGS=1
  IS_RELEASE=1
fi

if [[ "$PROJECT" == "oslo-incubator" ]]; then
  echo "Oslo-incubator mode: skipping tarball generation and upload"
  SKIPTARBALL=1
  SKIPUPLOAD=1
fi

title "Resolving $MILESTONE to version"
if [[ "$IS_RELEASE" == "1" ]]; then
  VERSION=$MILESTONE
  RELVERSION=$MILESTONE
else
  VERSION=`$TOOLSDIR/ms2version.py $PROJECT $MILESTONE`
  RELVERSION=${VERSION:0:8}
fi
echo "$MILESTONE is $VERSION (final being $RELVERSION)"

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
LANG=C git review -s
TARGETSHA=`git log -1 $SHA --format='%H'`
HEADSHA=`git log -1 HEAD --format='%H'`

title "Tagging $TARGETSHA as $VERSION"
if [[ "$IS_RELEASE" == "1" ]]; then
  TAGMSG="${PROJECT^} $VERSION release"
else
  TAGMSG="${PROJECT^} $MILESTONE milestone ($VERSION)"
fi
echo "Tag message is '$TAGMSG'"
if [[ "$TARGETSHA" != "$HEADSHA" ]]; then
  echo "Warning: target SHA does not correspond to HEAD"
fi
git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
git push gerrit $VERSION
REALSHA=`git show-ref -s --tags "$VERSION"`

title "Cleaning up"
cd ../..
rm -rf $MYTMPDIR

if [[ "$SKIPTARBALL" != "1" ]]; then
  title "Waiting for tarball from $REALSHA"
  $TOOLSDIR/wait_for_tarball.py $REALSHA

  title "Checking tarball is similar to last master.tar.gz"
  if [[ "$TARGETSHA" != "$HEADSHA" ]]; then
    echo "It will probably be a bit different since target is not HEAD."
  fi
  $TOOLSDIR/similar_tarballs.sh $PROJECT master $VERSION
  read -sn 1 -p "Press any key to continue..."
fi

if [[ "$SKIPBUGS" != "1" ]]; then
  title "Setting FixCommitted bugs to FixReleased"
  $TOOLSDIR/process_bugs.py $PROJECT --settarget=$MILESTONE --fixrelease
  read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
fi

if [[ "$SKIPUPLOAD" != "1" ]]; then
  title "Uploading tarball to Launchpad"
  if [[ "$IS_RELEASE" == "1" ]]; then
    $TOOLSDIR/upload_release.py $PROJECT $RELVERSION
  else
    $TOOLSDIR/upload_release.py $PROJECT $RELVERSION --milestone=$MILESTONE
  fi
else
  title "Marking milestone as released in Launchpad"
  $TOOLSDIR/upload_release.py $PROJECT $RELVERSION --milestone=$MILESTONE --nop
fi
