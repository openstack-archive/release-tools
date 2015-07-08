#!/bin/bash
#
# Script to release a project in one shot, including the git tag and
# launchpad updates.
#
# This script assumes that the project release manager follows pbr's
# SemVer rules for versioning and supports a launchpad project
# configured with a "next-$version" milestone (where $version is juno,
# kilo, etc.).
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

function clone_repo {
  title "Cloning repository for $PROJECT"
  git clone git://git.openstack.org/openstack/$REPO
  cd $REPO
  REPODIR="$(pwd)"
  git review -s
}

function pull_repo {
  git --git-dir "$REPODIR"/.git fetch
}

if [ $# -lt 4 ]; then
    echo "Usage: $0 series version SHA launchpad-project"
    echo
    echo "Example: $0 juno 1.0.0 HEAD oslo.rootwrap"
    exit 2
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

SERIES=$1
VERSION=$2
TARGET=$VERSION
SHA=$3
PROJECT=$4
EMAIL_TAGS="$5"
REPODIR=$6
if [ -n "REPODIR" ]; then
  REPODIR="$(realpath $REPODIR)"
fi

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RELNOTESDIR="$PWD/relnotes"
mkdir -p $RELNOTESDIR

setup_temp_space release-tag-$PROJECT

REPO=$(lp_project_to_repo $PROJECT)

# Extend the email tags or set a default tag for the project owner.
PROJECT_OWNER=${PROJECT_OWNER:-$($TOOLSDIR/get_project_for_repo.py --email-tag openstack/$REPO)}
if [[ "$PROJECT_OWNER" != "" ]]; then
    EMAIL_TAGS="${PROJECT_OWNER}${EMAIL_TAGS}"
fi

if [ -z "$REPODIR" ]; then
  clone_repo
else
  pull_repo
fi

cd $REPODIR

title "Sanity checking $VERSION"
if ! $TOOLSDIR/sanity_check_version.py $VERSION $(git tag)
then
    read -s -p "Press Ctrl-C to cancel or Return to continue..."
fi
TARGETSHA=`git log -1 $SHA --format='%H'`

title "Tagging $TARGETSHA as $VERSION"
TAGMSG="$PROJECT $VERSION release"

if git branch -a | grep -q origin/stable/$SERIES; then
    STABLE_BRANCH=1
else
    STABLE_BRANCH=0
fi

if git show-ref "$VERSION"
then
    echo "$PROJECT already has a version $VERSION tag"
else
    if [[ "$STABLE_BRANCH" != "0" ]]; then
        prev_series=origin/stable/$SERIES
        stable="--stable"
    else
        prev_series=""
        stable=""
    fi
    previous_rev=$(get_last_tag $prev_series)
    echo "Tag message is '$TAGMSG'"
    git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
    git push gerrit $VERSION
    title "Release notes"
    relnotes_file="$RELNOTESDIR/$PROJECT-$VERSION"
    if [[ "$EMAIL_TAGS" != "" ]]; then
        email_tags="--email-tags $EMAIL_TAGS"
    fi
    ${TOOLSDIR}/release_notes.py \
            --email \
            $email_tags \
            --series $SERIES \
            $stable \
            . $previous_rev $VERSION \
            --include-pypi-link \
        | tee $relnotes_file
fi

# Figure out if we have to rename a next-$SERIES milestone or if we
# should just create a new milestone.
MILESTONE_URL="https://launchpad.net/$PROJECT/+milestone/next-$SERIES"
if curl --silent --output /dev/null --fail "$MILESTONE_URL"; then
    title "Renaming next-$SERIES to $VERSION"
    $TOOLSDIR/rename_milestone.py $PROJECT next-$SERIES $VERSION
else
    title "Ensuring that milestone $VERSION exists"
    $TOOLSDIR/ensure_milestone.py $PROJECT $SERIES $VERSION
fi

title "Setting FixCommitted bugs to FixReleased"
if [[ "$STABLE_BRANCH" != "1" ]]; then
    $TOOLSDIR/process_bugs.py $PROJECT --settarget=$TARGET --fixrelease
    read -sn 1 -p "Fix any leftover bugs manually and press key to continue..."
    echo
else
    read -sn 1 -p "Make sure all closed bugs are properly targeted, then press key to continue..."
    echo
fi

title "Marking milestone as released in Launchpad"
$TOOLSDIR/close_milestone.py $PROJECT $TARGET
