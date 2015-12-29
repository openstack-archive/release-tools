#!/bin/bash
#
# Script to check the difference between produced tarball and git repository
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
git archive -o $TMPDIR/repo.tar HEAD
tar tf $TMPDIR/repo.tar | sort -g > $TMPDIR/repo.contents
python setup.py sdist > /dev/null 2>&1 || error "sdist failed"
tar tzf dist/*.tar.gz | cut -f2- -d/ | grep -v ^$ | sort -g > $TMPDIR/tarball.contents
pymodulename=${1//-/_}
diff -u0 $TMPDIR/repo.contents $TMPDIR/tarball.contents | grep -v '^@@' | grep -v "^+$1.egg-info/" | grep -v "^+$pymodulename.egg-info/" | grep -v '^+PKG-INFO' | tail -n +3
rm -rf $TMPDIR
