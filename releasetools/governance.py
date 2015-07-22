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


def get_repo_owner(repo_name):
    """Return the name of the team that owns the repository.

    :param repo_name: Long name of the repository, such as 'openstack/nova'.

    """
    team_data = get_team_data()
    for team, info in team_data.items():
        for project in info.get('projects', []):
            if project['repo'] == repo_name:
                return team
    raise ValueError('Repository %s not found in governance list' % repo_name)


def get_repositories(team, tags, code_only=False):
    """Return a sequence of repositories, possibly filtered.

    :param team: The name of the team owning the repositories. Can be
        None.
    :param tags: The names of any tags the repositories should
        have. Can be empty.
    :param code_only: Boolean indicating whether to return only code
      repositories (ignoring specs and cookiecutter templates).

    """
    team_data = get_team_data()

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
