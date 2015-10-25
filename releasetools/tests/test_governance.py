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

import textwrap

from oslotest import base
import yaml

from releasetools import governance

TEAM_TEXT = textwrap.dedent("""
    Cookies:
      ptl: Nobody
      deliverables:
        cookies:
          repos:
            - openstack-test/cookies-cookiecutter

    Barbican:
      ptl: Douglas Mendizabal (redrobot)
      irc-channel: openstack-barbican
      service: Key management service
      mission: >
        To produce a secret storage and generation system capable
        of providing key management for services wishing to enable
        encryption features.
      url: https://wiki.openstack.org/wiki/Barbican
      deliverables:
        barbican:
          repos:
            - openstack/barbican
          tags:
            - release:cycle-with-milestones
            - release:has-stable-branches
            - release:managed
            - type:service
        barbican-specs:
          repos:
            - openstack/barbican-specs
        castellan:
          repos:
            - openstack/castellan
          tags:
            - release:independent
            - type:library
        kite:
          repos:
            - openstack/kite
          tags:
            - type:service
        python-barbicanclient:
          repos:
            - openstack/python-barbicanclient
          tags:
            - release:cycle-with-intermediary
            - release:has-stable-branches
            - release:managed
            - type:library
        python-kiteclient:
          repos:
            - openstack/python-kiteclient
          tags:
            - type:library

    Cinder:
      ptl: Mike Perez (thingee)
      irc-channel: openstack-cinder
      service: Block Storage
      mission: >
        To implement services and libraries to provide on-demand,
        self-service access to Block Storage resources via
        abstraction and automation on top of
        other block storage devices.
      url: https://wiki.openstack.org/wiki/Cinder
      tags:
        - team:diverse-affiliation
      deliverables:
        cinder:
          repos:
            - openstack/cinder
          tags:
            - tc-approved-release
            - release:managed
            - release:cycle-with-milestones
            - release:has-stable-branches
            - type:service
            - vulnerability:managed
        cinder-specs:
          repos:
            - openstack/cinder-specs
        os-brick:
          repos:
            - openstack/os-brick
          tags:
            - release:cycle-with-intermediary
            - type:library
            - release:managed
        python-cinderclient:
          repos:
            - openstack/python-cinderclient
          tags:
            - release:cycle-with-intermediary
            - release:has-stable-branches
            - type:library
            - release:managed
            - vulnerability:managed
""")

TEAM_DATA = yaml.load(TEAM_TEXT)


class GetRepositoriesTest(base.BaseTestCase):

    def test_all(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            None,
            None,
            [],
            code_only=False,
        )
        repo_names = sorted(r.name for r in repos)
        self.assertEqual(
            sorted(['openstack/barbican',
                    'openstack/barbican-specs',
                    'openstack/python-barbicanclient',
                    'openstack/castellan',
                    'openstack/kite',
                    'openstack/python-kiteclient',
                    'openstack/cinder',
                    'openstack/cinder-specs',
                    'openstack/os-brick',
                    'openstack/python-cinderclient',
                    'openstack-test/cookies-cookiecutter']),
            repo_names,
        )

    def test_code_only(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            None,
            None,
            [],
            code_only=True,
        )
        repo_names = sorted(r.name for r in repos)
        self.assertEqual(
            sorted(['openstack/barbican',
                    'openstack/python-barbicanclient',
                    'openstack/castellan',
                    'openstack/kite',
                    'openstack/python-kiteclient',
                    'openstack/cinder',
                    'openstack/os-brick',
                    'openstack/python-cinderclient']),
            repo_names,
        )

    def test_team_name(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            'Cookies',
            None,
            [],
            code_only=False,
        )
        repo_names = [r.name for r in repos]
        self.assertEqual(
            ['openstack-test/cookies-cookiecutter'],
            repo_names,
        )

    def test_team_tag(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            None,
            None,
            ['team:diverse-affiliation'],
            code_only=False,
        )
        repo_names = sorted(r.name for r in repos)
        self.assertEqual(
            sorted(['openstack/cinder',
                    'openstack/cinder-specs',
                    'openstack/os-brick',
                    'openstack/python-cinderclient']),
            repo_names,
        )

    def test_deliverable_tag(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            None,
            None,
            ['tc-approved-release'],
            code_only=False,
        )
        repo_names = sorted(r.name for r in repos)
        self.assertEqual(
            ['openstack/cinder'],
            repo_names,
        )

    def test_deliverable_name(self):
        repos = governance.get_repositories(
            TEAM_DATA,
            None,
            'cookies',
            [],
            code_only=False,
        )
        repo_names = sorted(r.name for r in repos)
        self.assertEqual(
            ['openstack-test/cookies-cookiecutter'],
            repo_names,
        )


class GetRepoOwnerTest(base.BaseTestCase):

    def test(self):
        owner = governance.get_repo_owner(
            TEAM_DATA,
            'openstack/cinder',
        )
        self.assertEqual('Cinder', owner)
