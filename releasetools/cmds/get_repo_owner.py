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

"""Print the name of the project that owns a repository.
"""

from __future__ import print_function

import argparse

from releasetools import governance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--email-tag',
        action='store_true',
        default=False,
        help='print as an email tag for release notes',
    )
    parser.add_argument(
        'repository',
        help='the name of the repository, such as "openstack/nova"',
    )
    args = parser.parse_args()

    team_data = governance.get_team_data()
    try:
        name = governance.get_repo_owner(team_data, args.repository)
    except ValueError as e:
        parser.error(str(e))
    else:
        if args.email_tag:
            name = '[' + name.split(' ')[0].lower() + ']'
        print(name)
