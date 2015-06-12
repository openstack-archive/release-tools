#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in all
# libraries, so we don't have to remember the incantation.

if [[ $# -gt 1 ]]; then
    echo "Usage: $(basename $0) <branch>"
    exit 1
fi

SERIES=${1:-master}

TOOLSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $TOOLSDIR/functions

PROJECT_CONFIG_DIR=${PROJECT_CONFIG_DIR:-${TOOLSDIR}/../../openstack-infra/project-config}

repos="$(cd $PROJECT_CONFIG_DIR && grep 'pushSignedTag = group library-release' gerrit/acls/openstack/*.config  | cut -f1 -d: | sed -e 's|gerrit/acls/||' -e 's/.config$//')"
if [[ -z "$repos" ]]; then
    echo "No repositories were found by scanning $PROJECT_CONFIG_DIR" 1>&2
    exit 1
fi

$(dirname $0)/list_unreleased_changes.sh $SERIES $repos
