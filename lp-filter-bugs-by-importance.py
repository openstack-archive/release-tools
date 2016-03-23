#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
This Launchpad tool is used to reset <release>-backport-potential tags once
backports are merged.
"""

import argparse
import sys

from launchpadlib.launchpad import Launchpad


VALID_IMPORTANCES = ('Undecided', 'Wishlist', 'Low', 'Normal', 'High', 'Critical')


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Filter out bugs of specified importance.')
    parser.add_argument(
        'project', help='Launchpad project name')
    parser.add_argument(
        '--importance',
        nargs='?', choices=VALID_IMPORTANCES, default='Wishlist',
        help='Bug importance to filter')
    return parser.parse_args()


def _filter_bugs(lp, project, importance, bugs):
    return [
        bug
        for bug in bugs
        for task in lp.bugs[bug].bug_tasks
        if task.bug_target_name == project and task.importance != importance
    ]


def main():
    args = _parse_args()

    lp = Launchpad.login_with('filter-bugs-by-importance', 'production')

    bugs = [line.strip() for line in sys.stdin.readlines()]
    bugs = _filter_bugs(lp, args.project, args.importance, bugs)
    print(' '.join(bugs))


if __name__ == '__main__':
    main()
