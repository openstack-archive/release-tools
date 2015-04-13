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

# Initial transifex setup
function setup_translation {
    # Track in HAS_CONFIG whether we run "tx init" since calling it
    # will add the file .tx/config - and "tx set" might update it. If
    # "tx set" updates .tx/config, we need to handle the file if it
    # existed before.
    HAS_CONFIG=1

    # Initialize the transifex client, if there's no .tx directory
    if [ ! -d .tx ] ; then
        tx init --host=https://www.transifex.com
        HAS_CONFIG=0
    fi
}

# Setup a project for transifex
function setup_project {
    local project=$1

    # Transifex project name does not include "."
    tx_project=${project/\./}
    tx set --auto-local -r ${tx_project}.${tx_project}-translations \
        "${project}/locale/<lang>/LC_MESSAGES/${project}.po" \
        --source-lang en \
        --source-file ${project}/locale/${project}.pot -t PO \
        --execute
}


# Propose patch using COMMIT_MSG
function send_patch {

    # Revert any changes done to .tx/config
    if [ $HAS_CONFIG -eq 1 ]; then
        git reset -q .tx/config
        git checkout -- .tx/config
    fi

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

# Setup transifex configuration for log level message translation.
# Needs variables setup via setup_loglevel_vars.
function setup_loglevel_project {
    project=$1

    # Transifex project name does not include "."
    tx_project=${project/\./}

    for level in $LEVELS ; do
        # Bootstrapping: Create file if it does not exist yet,
        # otherwise "tx set" will fail.
        if [ ! -e  ${project}/locale/${project}-log-${level}.pot ]; then
            touch ${project}/locale/${project}-log-${level}.pot
        fi
        tx set --auto-local -r ${tx_project}.${tx_project}-log-${level}-translations \
            "${project}/locale/<lang>/LC_MESSAGES/${project}-log-${level}.po" \
            --source-lang en \
            --source-file ${project}/locale/${project}-log-${level}.pot -t PO \
            --execute
    done
}

# Run extract_messages for user visible messages and log messages.
# Needs variables setup via setup_loglevel_vars.
function extract_messages_log {
    project=$1

    # Update the .pot files
    python setup.py extract_messages
    for level in $LEVELS ; do
        python setup.py extract_messages --no-default-keywords \
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
    for f in `git diff --cached --name-only`; do
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

    for i in `find $project/locale -name *.po `; do
        # Output goes to stderr, so redirect to stdout to catch it.
        trans=`msgfmt --statistics -o /dev/null $i 2>&1`
        check="^0 translated messages"
        if [[ $trans =~ $check ]] ; then
            # Nothing is translated, remove the file.
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
            let total=$trans_no+$untrans_no
            let ratio=100*$trans_no/$total
            # Since we only download files that are at least
            # translated to 75 per cent, let's delete those that have
            # signficantly less translations.
            # For now we delete files that suddenly are less than 20
            # per cent translated.
            if [[ "$ratio" -lt "66" ]] ; then
                git rm -f $i
            fi
        fi
    done
}

if [ $# -ne 1 ] ; then
   echo "Script needs to called with single argument: Name of current project"
   exit 1
fi

PROJECT=$1

# git checkout --track origin/proposed/kilo
git checkout proposed/kilo
git pull
git checkout -b translations

set +e
read -d '' COMMIT_MSG <<EOF
Release Import of Translations from Transifex

Manual import of Translations from Transifex. This change also removes
all po files that are less than 66 per cent translated since such
partially translated files will not help users.

This updates also recreates all pot (translation source files) to
reflect the state of the repository.

This change needs to be done manually since the automatic import does
not handle the proposed branches and we need to sync with latest
translations.

EOF
    set -e

# Setup basic connection for transifex.
setup_translation
# Project specific transifex setup.
setup_project "$PROJECT"

# Setup some global vars which will be used in the rest of the script.
setup_loglevel_vars
# Project specific transifex setup for log translations.
setup_loglevel_project "$PROJECT"

# Download new files that are at least 75 % translated.
# Also downloads updates for existing files that are at least 75 %
# translated.
tx pull -a -f --minimum-perc=75

# Pull upstream translations of all downloaded files but do not
# download new files.
tx pull -f

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

# Filter out commits we do not want.
filter_commits

# Remove obsolete files.
cleanup_po_files "$PROJECT"

# Prepare patch (commit)
send_patch
echo "Please review and submit changes:"
echo "Use git review proposed/kilo"
