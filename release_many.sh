#!/bin/bash
#
# Script to release several projects in one shot using release_library.sh
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

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <release-list>"
    exit 1
fi

INFILE=$1

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

IFS=$'\r\n'
GLOBIGNORE='*'
RELEASES=($(grep -v '^#' $INFILE))

DEFAULT_SERIES=liberty

IFS=$' '

for line in "${RELEASES[@]}"; do
    release=($(echo $line))
    version=${release[0]}
    hash=${release[1]}
    project=${release[2]}
    override_series=${release[3]}
    series=${override_series:-$DEFAULT_SERIES}
    title "$project @ $hash == $version ($series)"
    $TOOLSDIR/release_library.sh $series $version $hash $project
done
