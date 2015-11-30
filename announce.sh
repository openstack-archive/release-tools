#!/bin/bash
#
# Script to generate a release announcement for a project.
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
    echo "Usage: $0 path-to-repository [version] SHA"
    echo
    echo "Example: $0 ~/repos/openstack/oslo.rootwrap"
    echo "Example: $0 ~/repos/openstack/oslo.rootwrap 3.0.3"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

REPODIR=$1
VERSION=$2
SHORTNAME=`basename $REPO`

if [[ -z "$VIRTUAL_ENV" ]]; then
    (cd $TOOLSDIR && tox -e venv --notest)
    source $TOOLSDIR/.tox/venv/bin/activate
fi

# Make our output directory before we start moving around into
# temporary directories.
RELNOTESDIR="$PWD/relnotes"
mkdir -p $RELNOTESDIR

# Set up temporary directory for scratch files
setup_temp_space announce-$SHORTNAME

cd $REPODIR

# Determine the most recent tag if we weren't given a value.
if [[ -z "$VERSION" ]]; then
    VERSION=$(get_last_tag)
fi

# Look for the previous version on the same branch.
PREVIOUS_VERSION=$(git describe --abbrev=0 ${VERSION}^)

# Extract the tag message by parsing the git show output, which looks
# something like:
#
# tag 1.12.0
# Tagger: Doug Hellmann <doug@doughellmann.com>
# Date:   Wed Nov 25 19:52:19 2015 +0000
#
# os-client-config 1.12.0 release
# -----BEGIN PGP SIGNATURE-----
# Comment: GPGTools - http://gpgtools.org
#
# iQEcBAABAgAGBQJWVhFzAAoJEDttBqDEKEN6hf8H/3xqtcW4bDVkD0q2vu0+hK0C
#
GIT_MESSAGE=$(git show --no-patch "$VERSION" \
    | awk '
/^(tag|Tagger:|Date:|^$)/ {next}
/BEGIN PGP SIGNATURE/ {exit}
{ print }
')

# The series name is part of the commit message left by release.sh.
SERIES=$(echo $GIT_MESSAGE | awk '{ print $2 }')

# Figure out if that series is a stable branch or not.
if git branch -a | grep -q origin/stable/$SERIES; then
    stable="--stable"
fi

# Set up email tags for the project owner.
PROJECT_OWNER=${PROJECT_OWNER:-$(get-repo-owner --email-tag $REPO || echo "")}
if [[ "$PROJECT_OWNER" != "" ]]; then
    EMAIL_TAGS="${PROJECT_OWNER}${EMAIL_TAGS}"
fi

echo "$PREVIOUS_VERSION to $VERSION on $SERIES"

relnotes_file="$RELNOTESDIR/$SHORTNAME-$VERSION"

release-notes \
    --email \
    $email_tags \
    --series $SERIES \
    $stable \
    . $PREVIOUS_VERSION $VERSION \
    --include-pypi-link \
    | tee $relnotes_file

echo
echo $relnotes_file

exit 0
