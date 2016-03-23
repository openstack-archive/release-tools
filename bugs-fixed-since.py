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
This tool will list bugs that were fixed in project master.
"""

import argparse
import os.path
import re

from git import Repo


BUG_PATTERN = r'Bug:\s+#?(?P<bugnum>\d+)'


def _parse_args():
    parser = argparse.ArgumentParser(
        description='List bugs with recent fixes.')
    parser.add_argument(
        '--repo', '-r',
        default='.',
        help='path to the openstack project repository',
    )
    parser.add_argument(
        '--start', '-s', required=True,
        help='git hash to start search from')
    return parser.parse_args()


def _get_git_url(project):
    return 'https://git.openstack.org/openstack/%s' % project


def main():
    args = _parse_args()

    repo = Repo(args.repo)

    # make sure that we work with the latest code
    repo.remotes.origin.fetch()

    latest = repo.refs['origin/master'].commit
    rev = '%s..%s' % (args.start, latest.hexsha)

    # avoid duplicates
    bugs = set()

    for commit in repo.iter_commits(rev):
        for match in re.finditer(BUG_PATTERN, commit.message):
            bugs.add(match.group('bugnum'))

    for bug in bugs:
        print(bug)


if __name__ == '__main__':
    main()
