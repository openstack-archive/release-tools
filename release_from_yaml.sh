#!/bin/bash
#
# Script to release projects based on changes to the deliverables
# files in the openstack/releases repository.
#
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

if [ $# -lt 1 ]; then
    echo "Usage: $0 releases_repository [deliverable_files]"
    echo
    echo "Example: $0 ~/repos/openstack/releases"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

RELEASES_REPO="$1"
shift
DELIVERABLES="$@"

if [[ -z "$VIRTUAL_ENV" ]]; then
    (cd $TOOLSDIR && tox -e venv --notest)
    source $TOOLSDIR/.tox/venv/bin/activate
fi

list-deliverable-changes -r $RELEASES_REPO $DELIVERABLES \
| while read deliverable series version repo hash; do
    $TOOLSDIR/release.sh $repo $series $version $hash
done

exit 0
