#!/bin/bash
#
# Convenience wrapper to show the unreleased changes in Oslo
# libraries, so we don't have to remember the incantation.

if [[ $# -ne 1 ]]; then
    echo "Usage: $(basename $0) <branch>"
    exit 1
fi

repos="$(./list_repos_by_project.py --code-only Oslo | grep -v incubator)"

$(dirname $0)/list_unreleased_changes.sh $1 $repos
