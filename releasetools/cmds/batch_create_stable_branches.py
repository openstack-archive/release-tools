#!/usr/bin/env python

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

"""Generate the commands to create stable branches for a bunch of projects.
"""

from __future__ import print_function

import argparse
import glob
import os.path
import re
import subprocess

from releasetools import governance

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=governance.PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
    parser.add_argument(
        '--releases-repo', '-r',
        default='.',
        help='path to the releases repository for automatic scanning',
    )
    parser.add_argument(
        '--team',
        help='the name of the project team, such as "Nova" or "Oslo"',
    )
    parser.add_argument(
        '--tag',
        action='append',
        default=[],
        help='the name of a tag, such as "release:managed"',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='produce detailed output',
    )
    parser.add_argument(
        'series',
        help='the name of the release series to work on'
    )
    args = parser.parse_args()

    team_data = governance.get_team_data()
    if args.verbose:
        print('# Filtering on team: {}'.format(args.team))
        print('# Filtering on tags: {}'.format(args.tag))
    filtered_repos = {
        r.name
        for r in governance.get_repositories(
                team_data=team_data,
                team_name=args.team,
                tags=args.tag,
                code_only=True,
        )
    }

    pattern = os.path.join(args.releases_repo, 'deliverables',
                           args.series, '*.yaml')
    deliverable_files = sorted(glob.glob(pattern))

    for filename in deliverable_files:
        if args.verbose:
            print('\n# {}'.format(filename))
        with open(filename, 'r') as f:
            deliverable_data = yaml.safe_load(f)
        releases = deliverable_data.get('releases')
        if not releases:
            if args.verbose:
                print('#  no releases')
            continue
        latest_release = releases[-1]
        projects = latest_release.get('projects')
        if not projects:
            if args.verbose:
                print('#  no projects')
            continue
        for project in projects:
            repo = project['repo']
            if repo in filtered_repos:
                print('make_stable_branch.sh {series} {repo} {version}'.format(
                    series=args.series,
                    repo=repo,
                    version=latest_release['version'],
                ))
            elif args.verbose:
                print('#  {} does not match search criteria'.format(repo))

    return 0


if __name__ == '__main__':
    main()
