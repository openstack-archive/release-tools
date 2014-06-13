#!/bin/bash
#
# Script to tag RC for intermediary swift release
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
    echo "Usage: $0 SHA RC"
    echo
    echo "Example: $0 d0e1a2db 1.13.0"
    exit 2
fi

SHA=$1
VERSION=$2
RCVERSION="${VERSION}.rc1"

PROJECT="swift"
TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

title "Checking that milestone exists for $VERSION"
$TOOLSDIR/ms2version.py swift $VERSION

title "Cloning repository for $PROJECT"
MYTMPDIR=`mktemp -d`
cd $MYTMPDIR
git clone git://git.openstack.org/openstack/$PROJECT
cd $PROJECT
LANG=C git review -s
TARGETSHA=`git log -1 $SHA --format='%H'`
HEADSHA=`git log -1 HEAD --format='%H'`

title "Tagging $TARGETSHA as $RCVERSION"
TAGMSG="${PROJECT^} $MILESTONE"
echo "Tag message is '$TAGMSG'"
if [[ "$TARGETSHA" != "$HEADSHA" ]]; then
  echo "Warning: target SHA does not correspond to HEAD"
fi
git tag -m "$TAGMSG" -s "$RCVERSION" $TARGETSHA
git push gerrit $RCVERSION
REALSHA=`git show-ref -s "$RCVERSION"`

title "Waiting for tarball from $REALSHA"
$TOOLSDIR/wait_for_tarball.py $REALSHA

title "Checking tarball is similar to last master.tar.gz"
if [[ "$TARGETSHA" != "$HEADSHA" ]]; then
  echo "It will probably be a bit different since target is not HEAD."
fi
$TOOLSDIR/similar_tarballs.sh $PROJECT master $RCVERSION
read -sn 1 -p "Press any key to continue..."

title "Setting FixCommitted bugs to FixReleased"
$TOOLSDIR/process_bugs.py $PROJECT --settarget=$MILESTONE --fixrelease

title "Cleaning up"
cd ../..
rm -rf $MYTMPDIR
