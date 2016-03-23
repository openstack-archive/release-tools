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
This tool will transform bug numbers into proper Launchpad links.
"""

import argparse
import sys

from launchpadlib.launchpad import Launchpad


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Dump useful bug info.')
    parser.add_argument(
        'project', help='Launchpad project name')
    return parser.parse_args()


def _annotate_bug(lp, project, bugnum):
    bug = lp.bugs[bugnum]
    for task in bug.bug_tasks:
        if task.bug_target_name == project:
            break
    else:
        return

    print(
        '%(url)s "%(title)s" (%(importance)s,%(status)s) [%(tags)s] [%(assignee)s]' %
        {'url': 'https://bugs.launchpad.net/bugs/%s' % bugnum,
         'title': bug.title,
         'importance': task.importance,
         'status': task.status,
         'tags': ','.join(bug.tags),
         'assignee': task.assignee.name})


def main():
    args = _parse_args()

    lp = Launchpad.login_with('filter-bugs-by-importance', 'production')

    for line in sys.stdin.readlines():
        bugnum = line.strip()
        _annotate_bug(lp, args.project, bugnum)


if __name__ == '__main__':
    main()
