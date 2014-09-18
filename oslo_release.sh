#!/bin/bash
#
# Script to release an Oslo library in one shot
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

if [ $# -lt 4 ]; then
    echo "Usage: $0 series version SHA project"
    echo
    echo "Example: $0 juno 1.0.0 HEAD oslo.rootwrap"
    exit 2
fi

SERIES=$1
VERSION=$2
TARGET=$VERSION
SHA=$3
PROJECT=$4

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function title {
  echo
  echo "$(tput bold)$(tput setaf 1)[ $1 ]$(tput sgr0)"
}

if [[ $VERSION == *a* ]]; then
    ALPHA_RELEASE=1
    TARGET="next-$SERIES"
fi

MYTMPDIR=`mktemp -d release-tag-XXX`
function cleanup_tmp {
    title "Cleaning up"
    cd /tmp
    rm -rf $MYTMPDIR
}
trap cleanup_tmp EXIT
cd $MYTMPDIR

# Some of the repository names don't match the launchpad names.
REPO=$(echo $PROJECT | sed -e 's|python-||')

title "Cloning repository for $PROJECT"
git clone git://git.openstack.org/openstack/$REPO
cd $REPO
git review -s

if git show-ref "$VERSION"
then
    title "Version $VERSION is already tagged in this repository"
    read -s -p "Press Ctrl-C to cancel or Return to continue..."
else
    TARGETSHA=`git log -1 $SHA --format='%H'`

    title "Tagging $TARGETSHA as $VERSION"
    if [[ "$ALPHA_RELEASE" != "1" ]]; then
        TAGMSG="$PROJECT $VERSION release"
    else
        TAGMSG="$PROJECT $VERSION alpha milestone"
    fi
    echo "Tag message is '$TAGMSG'"
    git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
    git push gerrit $VERSION
fi

if [[ "$ALPHA_RELEASE" != "1" ]]; then
  title "Renaming next-$SERIES to $VERSION"
  $TOOLSDIR/rename_milestone.py $PROJECT next-$SERIES $VERSION
fi

title "Setting FixCommitted bugs to FixReleased"
$TOOLSDIR/process_bugs.py $PROJECT --settarget=$TARGET --fixrelease
read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
echo

if [[ "$ALPHA_RELEASE" != "1" ]]; then
  title "Marking milestone as released in Launchpad"
  $TOOLSDIR/upload_release.py $PROJECT $VERSION --milestone=$TARGET --nop
fi
