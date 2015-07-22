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

"""Work with the governance repository.
"""

from __future__ import print_function

import argparse
import itertools
import requests
import yaml

PROJECTS_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml"  # noqa


def get_team_data(url=PROJECTS_LIST):
    """Return the parsed team data from the governance repository.

    :param url: Optional URL to the location of the projects.yaml
        file. Defaults to the most current version in the public git
        repository.

    """
    r = requests.get(url)
    return yaml.load(r.text)


def get_repositories(team, tags, code_only=False, url=PROJECTS_LIST):
    """Return a sequence of repositories, possibly filtered.

    :param team: The name of the team owning the repositories. Can be
        None.
    :param tags: The names of any tags the repositories should
        have. Can be empty.
    :param code_only: Boolean indicating whether to return only code
      repositories (ignoring specs and cookiecutter templates).

    """
    team_data = get_team_data(url)

    if team is not None:
        if team not in team_data:
            raise ValueError('No team %r found in the project list' % team)
        projects = team_data[team].get('projects', [])
    else:
        projects = itertools.chain(
            *[t.get('projects', []) for t in team_data.values()]
        )

    if code_only:
        projects = (
            p
            for p in projects
            if (not p['repo'].endswith('-specs')
                and 'cookiecutter' not in p['repo'])
        )

    if tags:
        tags = set(tags)
        projects = (
            p
            for p in projects
            if tags.issubset(set(t['name']
                                 for t in p.get('tags', [])))
        )

    return list(projects)


def list_repos():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=PROJECTS_LIST,
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
        '--tag',
        action='append',
        default=[],
        help='the name of a tag, such as "release:managed"',
    )
    args = parser.parse_args()

    repos = get_repositories(args.team, args.tag, code_only=args.code_only)
    for repo in repos:
        print(repo['repo'])
