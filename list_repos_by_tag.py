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

"""Print a list of the repositories with a given tag.
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
        'tag',
        help='the name of the tag, such as "release:managed"',
    )
    args = parser.parse_args()

    r = requests.get(args.project_list)
    project_data = yaml.load(r.text)

    for project, info in project_data.items():
        for repo in info['projects']:
            for tag in repo.get('tags', []):
                if tag['name'] == args.tag:
                    print(repo['repo'])


if __name__ == '__main__':
    main()
