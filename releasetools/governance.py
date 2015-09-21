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

import weakref

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


def get_repo_owner(team_data, repo_name):
    """Return the name of the team that owns the repository.

    :param team_data: The result of calling :func:`get_team_data`
    :param repo_name: Long name of the repository, such as 'openstack/nova'.

    """
    for team, info in team_data.items():
        for dname, dinfo in info.get('deliverables', {}).items():
            if repo_name in dinfo.get('repos', []):
                return team
    raise ValueError('Repository %s not found in governance list' % repo_name)


class Team(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.deliverables = {
            dn: Deliverable(dn, di, self)
            for dn, di in self.data.get('deliverables', {}).items()
        }

    @property
    def tags(self):
        return set(self.data.get('tags', []))


class Deliverable(object):
    def __init__(self, name, data, team):
        self.name = name
        self.data = data
        self.team = weakref.proxy(team)
        self.repositories = {
            rn: Repository(rn, self)
            for rn in self.data.get('repos', [])
        }

    @property
    def tags(self):
        return set(self.data.get('tags', [])).union(self.team.tags)


class Repository(object):
    def __init__(self, name, deliverable):
        self.name = name
        self.deliverable = weakref.proxy(deliverable)

    @property
    def tags(self):
        return self.deliverable.tags

    @property
    def code_related(self):
        return not (self.name.endswith('-specs')
                    or 'cookiecutter' in self.name)


def get_repositories(team_data, team_name=None, deliverable_name=None,
                     tags=[], code_only=False):
    """Return a sequence of repositories, possibly filtered.

    :param team_data: The result of calling :func:`get_team_data`
    :param team_name: The name of the team owning the repositories. Can be
        None.
    :para deliverable_name: The name of the deliverable to which all
       repos should belong.
    :param tags: The names of any tags the repositories should
        have. Can be empty.
    :param code_only: Boolean indicating whether to return only code
      repositories (ignoring specs and cookiecutter templates).

    """
    if tags:
        tags = set(tags)
    if team_name:
        try:
            teams = [Team(team_name, team_data[team_name])]
        except KeyError:
            raise RuntimeError('No team %r found in %r' %
                               (team_name, list(team_data.keys())))
    else:
        teams = [Team(n, i) for n, i in team_data.items()]
    for team in teams:
        if deliverable_name and deliverable_name not in team.deliverables:
            continue
        if deliverable_name:
            deliverables = [team.deliverables[deliverable_name]]
        else:
            deliverables = team.deliverables.values()
        for deliverable in deliverables:
            for repository in deliverable.repositories.values():
                if tags and not tags.issubset(repository.tags):
                    continue
                if code_only and not repository.code_related:
                    continue
                yield repository
