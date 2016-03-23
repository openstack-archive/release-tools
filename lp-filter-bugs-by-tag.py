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
This Launchpad tool is used to filter out bugs by tag.
"""

import argparse
import sys

from launchpadlib.launchpad import Launchpad


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Filter out bugs with specified tag.')
    parser.add_argument(
        'project', help='Launchpad project name')
    parser.add_argument(
        'tag', nargs='?',
        help='Tag to filter')
    return parser.parse_args()


def _filter_bugs(lp, project, tag, bugs):
    return [
        bug
        for bug in bugs
        for task in lp.bugs[bug].bug_tasks
        if task.bug_target_name == project and tag not in lp.bugs[bug].tags
    ]


def main():
    args = _parse_args()

    lp = Launchpad.login_with('openstack-releasing', 'production')

    bugs = [line.strip() for line in sys.stdin.readlines()]
    for bug in _filter_bugs(lp, args.project, args.tag, bugs):
        print(bug)


if __name__ == '__main__':
    main()
