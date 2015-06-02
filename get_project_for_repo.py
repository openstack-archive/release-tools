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

"""Print the name of the project that owns a repository.
"""

from __future__ import print_function

import argparse
import requests
import yaml

PROJECTS_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml"  # noqa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
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

    r = requests.get(args.project_list)
    project_data = yaml.load(r.text)

    repos_to_proj = {}
    for p, pdata in project_data.items():
        for r in pdata['projects']:
            repos_to_proj[r['repo']] = p

    if args.repository not in repos_to_proj:
        parser.error('Repository %r not found in the project list' % args.repository)

    name = repos_to_proj[args.repository]
    if args.email_tag:
        name = '[' + name.split(' ')[0].lower() + ']'
    print(name)


if __name__ == '__main__':
    main()
