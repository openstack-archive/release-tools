#!/bin/bash -xe

# This code uses functions from propose_translation_update.sh,
# upstream_translation_update.sh, and common_translation_update.sh
# from project-config repository adjusted for import and cleanup of
# translated files for OpenStack Releases.

# Run this script locally from a project config and have credentials
# for Transifex set up and the transifex-client (tx) in your
# environment.

# This script does not work with Horizon and django_openstack_auth
# projects or with Documentation projects.

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 series projectname"
    echo
    echo "Example: $0 kilo keystone"
    exit 2
fi

SERIES=$1
PROJECT=$2
#BRANCH="stable/$SERIES"
BRANCH=$SERIES

PATH_CREATE_ZANATA="/home/aj/Software/vcs/OpenStack/openstack-infra/project-config/jenkins/scripts/"
QUIET="--quiet"

# Setup a project for Zanata
function setup_project {
    local project=$1
    local version=${2:-master}

    $PATH_CREATE_ZANATA/create-zanata-xml.py -p $project \
        -v $version --srcdir ${project}/locale --txdir ${project}/locale \
        -f zanata.xml --no-verify
}

# Propose patch using COMMIT_MSG
function send_patch {

    # Don't send a review if nothing has changed.
    if [ `git diff --cached |wc -l` -gt 0 ]; then
        # Commit and review
        git commit -F- <<EOF
$COMMIT_MSG
EOF

    fi
}

# Setup global variables LEVELS and LKEYWORDS
function setup_loglevel_vars {
    # Strings for various log levels
    LEVELS="info warning error critical"
    # Keywords for each log level:
    declare -g -A LKEYWORD
    LKEYWORD['info']='_LI'
    LKEYWORD['warning']='_LW'
    LKEYWORD['error']='_LE'
    LKEYWORD['critical']='_LC'
}


# Run extract_messages for user visible messages and log messages.
# Needs variables setup via setup_loglevel_vars.
function extract_messages_log {
    project=$1

    # Update the .pot files
    python setup.py $QUIET extract_messages --keyword "_C:1c,2 _P:1,2"
    for level in $LEVELS ; do
        python setup.py $QUIET extract_messages --no-default-keywords \
            --keyword ${LKEYWORD[$level]} \
            --output-file ${project}/locale/${project}-log-${level}.pot
    done
}

# Filter out files that we do not want to commit
function filter_commits {
    # Don't add new empty files.
    for f in `git diff --cached --name-only --diff-filter=A`; do
        # Files should have at least one non-empty msgid string.
        if ! grep -q 'msgid "[^"]' "$f" ; then
            git reset -q "$f"
            rm "$f"
        fi
    done

    # Don't send files where the only things which have changed are
    # the creation date, the version number, the revision date,
    # comment lines, or diff file information.
    for f in $(git diff --cached --name-only --diff-filter=AM); do
        # It's ok if the grep fails
        set +e
        changed=$(git diff --cached "$f" \
            | egrep -v "(POT-Creation-Date|Project-Id-Version|PO-Revision-Date)" \
            | egrep -c "^([-+][^-+#])")
        set -e
        if [ $changed -eq 0 ]; then
            git reset -q "$f"
            git checkout -- "$f"
        fi
    done
}

# Remove obsolete files. We might have added them in the past but
# would not add them today, so let's eventually remove them.
function cleanup_po_files {
    local project=$1

    # Note that the po files do not contain untranslated strings, we need
    # the pot file to figure out the total number of strings.
    for s in `find $project/ -name *.pot`; do
        bs=`basename $s`
        trans=`msgfmt --statistics -o /dev/null $s 2>&1`
        if [[ $trans =~ " untranslated message" ]] ; then
            total_no=`echo $trans|sed -e 's/^.* \([0-9]*\) untranslated message.*/\1/'`
        else
            total_no=0
        fi
        echo "$bs $total_no"
        if [ $total_no -eq 0 ] ; then
            continue
        fi
        po=${bs/.pot/.po}
        for i in `find $project/ -name $po `; do
            # Output goes to stderr, so redirect to stdout to catch it.
            trans=`msgfmt --statistics -o /dev/null $i 2>&1`
            check="^0 translated messages"
            if [[ $trans =~ $check ]] ; then
                # Nothing is translated, remove the file.
                echo "Nothing translated"
                git rm -f $i
            else
                if [[ $trans =~ " translated message" ]] ; then
                    trans_no=`echo $trans|sed -e 's/ translated message.*$//'`
                else
                    trans_no=0
                fi
                if [[ $trans =~ " untranslated message" ]] ; then
                    untrans_no=`echo $trans|sed -e 's/^.* \([0-9]*\) untranslated message.*/\1/'`
                else
                    untrans_no=0
                fi
                let ratio=100*$trans_no/$total_no
                # Since we only download files that are at least
                # translated to 75 per cent, let's delete those that have
                # signficantly less translations.
                # For now we delete files that suddenly are less than 66
                # per cent translated.
                if [[ "$ratio" -lt "66" ]] ; then
                    git rm -f $i
                    echo "Removed $i with $ratio %"
                fi
            fi
        done
    done
}

# Reduce size of po files. This reduces the amount of content imported
# and makes for fewer imports.
# This does not touch the pot files. This way we can reconstruct the po files
# using "msgmerge POTFILE POFILE -o COMPLETEPOFILE".
function compress_po_files {
    local directory=$1

    for i in $(find $directory -name *.po) ; do
        msgattrib --translated --no-location --sort-output "$i" \
            --output="${i}.tmp"
        mv "${i}.tmp" "$i"
    done
}

# Note: Branch need to be exists, you can create it with:
# git checkout --track origin/$BRANCH

git checkout $BRANCH
git pull
git checkout -B translations

# For partial translations and choosing 75% , see
# https://bugs.launchpad.net/horizon/+bug/1317794.  The number 66 %
# was choosen for releases so that partial translation does not get
# removed due to last minute string changes.

set +e
read -d '' COMMIT_MSG <<EOF
Cleanup of Translations

In preparation for the release, do some cleanups for translations.

Removes all po files that are partially translated. The translation
team has decided to exclude files with less than 66 % of translated
content. There is no content lost, all data is in the translation
server, we just remove it from the repository.

This updates also recreates all pot (translation source files) to
reflect the state of the repository.

This change needs to be done manually since the automatic import does
not handle some of these cases.

EOF
    set -e

# Project specific transifex setup.
setup_project "$PROJECT"

# Setup some global vars which will be used in the rest of the script.
setup_loglevel_vars

# Extract all messages from project, including log messages.
extract_messages_log "$PROJECT"

# Update existing translation files with extracted messages.
PO_FILES=`find ${PROJECT}/locale -name "${PROJECT}.po"`
if [ -n "$PO_FILES" ]; then
    # Use updated .pot file to update translations
    python setup.py update_catalog --no-fuzzy-matching  --ignore-obsolete=true
fi
# We cannot run update_catalog for the log files, since there is no
# option to specify the keyword and thus an update_catalog run would
# add the messages with the default keywords. Therefore use msgmerge
# directly.
for level in $LEVELS ; do
    PO_FILES=`find ${PROJECT}/locale -name "${PROJECT}-log-${level}.po"`
    if [ -n "$PO_FILES" ]; then
        for f in $PO_FILES ; do
            echo "Updating $f"
            msgmerge --update --no-fuzzy-matching $f \
                --backup=none \
                ${PROJECT}/locale/${PROJECT}-log-${level}.pot
            # Remove obsolete entries
            msgattrib --no-obsolete --force-po \
                --output-file=${f}.tmp ${f}
            mv ${f}.tmp ${f}
        done
    fi
done

# Add all changed files to git.
git add $PROJECT/locale/*

# Remove obsolete files.
cleanup_po_files "$PROJECT"

compress_po_files "$PROJECT"

# Some files were changed, add changed files again to git, so that we
# can run git diff properly.
git add $PROJECT/locale/*

# Filter out commits we do not want.
filter_commits

# Prepare patch (commit)
send_patch
echo "Please review change and then submit changes using:"
echo "  git review $BRANCH"
