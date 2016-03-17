#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in all projects
# claiming to have stable branches, so we don't have to remember the
# incantation.

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename $0) <branch>"
    exit 1
fi

if [[ -z "$VIRTUAL_ENV" ]]; then
    tox -e venv --notest
    source ./.tox/venv/bin/activate
fi

repos="$(list-repos --tag stable:follows-policy)"

# NOTE(tonyb): The purpose of this script is to 'quick check' for unreleased
# changes.  Without an email address release-notes will barf so set a fake
# email address if one isn't already present.
export EMAIL=${EMAIL:-noone@nowhere.com}
$(dirname $0)/list_unreleased_changes.sh $1 $repos
