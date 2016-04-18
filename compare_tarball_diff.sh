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

function error {
    echo ERROR: $1
    rm -rf $TMPDIR
    exit 1
}

if [ $# -lt 2 ]; then
    echo "Usage: $0 projectname branchname"
    exit 2
fi

TMPDIR=`mktemp -d`
git clone -b $2 https://git.openstack.org/openstack/$1 $TMPDIR/repo || error "clone failed"
cd $TMPDIR/repo
python setup.py sdist > /dev/null 2>&1 || error "sdist failed"
cd dist/
DIST_FILE=$(ls -1 *.tar.gz | head -1)
echo "Downloading remote file"
wget -q -O remote.tar.gz http://tarballs.openstack.org/$1/$DIST_FILE
mkdir local/
tar -C local/ -xzf $DIST_FILE
mkdir remote/
tar -C remote/ -xzf remote.tar.gz
echo "Running diff between remote and local tarballs"
echo "================== Begin Diff =================="
diff -Bbwurd local/ remote/
echo "=================== End Diff ==================="