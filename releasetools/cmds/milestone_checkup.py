#!/usr/bin/env python
#
# Script to verify state of projects that should have tagged a milestone.
#
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

from __future__ import print_function
import argparse
import os

from releasetools import governance

import yaml


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description='check milestone tag status')
    parser.add_argument(
        'releases_repo',
        help='path to the local copy of the releases repository',
    )
    parser.add_argument(
        'series',
        help='series to check, e.g. "newton"',
    )
    parser.add_argument(
        'milestone',
        help='milestone to check, e.g. "2"',
    )
    parser.add_argument(
        '--project-list',
        default=governance.PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
    args = parser.parse_args()

    team_data = governance.get_team_data(url=args.project_list)
    teams = {
        n: governance.Team(n, v)
        for n, v
        in team_data.items()
    }

    deliverable_base = os.path.join(
        args.releases_repo,
        'deliverables',
        args.series,
    )

    expected_tag_ending = '0b%s' % args.milestone

    for _, team in sorted(teams.items()):
        for dn, deliverable in sorted(team.deliverables.items()):
            if 'release:cycle-with-milestones' not in deliverable.tags:
                continue
            print('%s (%s)' % (deliverable.name, team.name))
            deliverable_filename = os.path.join(
                deliverable_base,
                deliverable.name + '.yaml',
            )
            if not os.path.exists(deliverable_filename):
                print('  did not find %s' % deliverable_filename)
            else:
                with open(deliverable_filename, 'r') as f:
                    deliverable_data = yaml.safe_load(f.read())
                for release in deliverable_data.get('releases', []):
                    if release['version'].endswith(expected_tag_ending):
                        break
                else:  # no break
                    versions = ', '.join([
                        str(r['version'])
                        for r in deliverable_data.get('releases', [])
                    ])
                    print('  did not find %s among existing releases: %s' % (
                        expected_tag_ending, versions))
            print()
