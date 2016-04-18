#!/bin/bash
#
# Script to check the difference between produced and uploaded tarballs
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

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

function error {
    echo ERROR: $1
    exit 1
}

if [ $# -lt 2 ]; then
    echo "Usage: $0 repo version"
    exit 2
fi

REPO=$1
VERSION=$2
PROJECT=$(basename $REPO)

setup_temp_space compare-tarball-diff

title "Testing $PROJECT $VERSION from $REPO"

cd $MYTMPDIR

clone_repo $REPO || error "clone failed"
cd $REPO
echo "Checking out $VERSION"
git checkout $VERSION || error "could not checkout $VERSION"

python setup.py sdist > /dev/null 2>&1 || error "sdist failed"

cd dist/
DIST_FILE=$(ls -1 *.tar.gz | head -1)

mkdir local/
tar -C local/ -xzf $DIST_FILE

URL="http://tarballs.openstack.org/$PROJECT/$DIST_FILE"
echo "Downloading and extracting $URL"
wget -q -O remote.tar.gz $URL || error "could not download existing tarball"

mkdir remote/
tar -C remote/ -xzf remote.tar.gz

echo "Comparing"
diff -Bbwurd local/ remote/
