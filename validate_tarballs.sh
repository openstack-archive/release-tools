#!/bin/bash
#
# Script to check the difference between produced and uploaded tarballs
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

function usage {
    echo "Usage: validate_tarballs.sh releases_repository series [deliverable_files]"
    echo
    echo "Example: validate_tarballs.sh ~/repos/openstack/releases mitaka"
}

if [ $# -lt 2 ]; then
    echo "ERROR: Please specify releases_repository and series"
    echo
    usage
    exit 1
fi

RELEASES_REPO="$1"
SERIES="$2"

latest-deliverable-versions -r $RELEASES_REPO $SERIES \
| while read repo version; do
    $TOOLSDIR/compare_tarball_diff.sh $repo $version
done

exit 0
