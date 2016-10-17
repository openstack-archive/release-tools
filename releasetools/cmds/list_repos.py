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
import operator

from releasetools import governance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=governance.PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
    parser.add_argument(
        '--code-only',
        default=False,
        action='store_true',
        help='only show repositories containing code, not docs or templates',
    )
    parser.add_argument(
        '--team',
        help='the name of the project team, such as "Nova" or "Oslo"',
    )
    parser.add_argument(
        '--deliverable',
        help='the name of the deliverable, such as "nova" or "oslo.config"',
    )
    parser.add_argument(
        '--tag',
        action='append',
        default=[],
        help='the name of a tag, such as "release:managed"',
    )
    parser.add_argument(
        '--cycle-based',
        action='store_true',
        default=False,
        help='include all cycle-based code repositories',
    )
    args = parser.parse_args()

    team_data = governance.get_team_data(url=args.project_list)
    repos = governance.get_repositories(
        team_data,
        args.team,
        args.deliverable,
        args.tag,
        code_only=args.code_only,
        cycle_based=args.cycle_based,
    )
    for repo in sorted(repos, key=operator.attrgetter('name')):
        print(repo.name)
