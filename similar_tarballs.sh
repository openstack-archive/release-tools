#!/bin/bash
#
# Script to check the difference between produced tarballs contents
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

if [ $# -lt 3 ]; then
    echo "Usage: $0 projectname tarballname tarballname"
    exit 2
fi

project=$1
tarball1=$2
tarball2=$3

TMPDIR=`mktemp -d`
wget -q http://tarballs.openstack.org/$project/$project-$tarball1.tar.gz -O $TMPDIR/tarball1.tar.gz
echo -n "$tarball1 "
md5sum $TMPDIR/tarball1.tar.gz | awk '{ print $1 }'
wget -q http://tarballs.openstack.org/$project/$project-$tarball2.tar.gz -O $TMPDIR/tarball2.tar.gz
echo -n "$tarball2 "
md5sum $TMPDIR/tarball2.tar.gz | awk {' print $1 }'
echo ----------------
tardiff -m $TMPDIR/tarball1.tar.gz $TMPDIR/tarball2.tar.gz
rm -rf $TMPDIR
