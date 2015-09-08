#!/usr/bin/env python
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

from oslotest import base
import testscenarios

from releasetools import semver


load_tests = testscenarios.load_tests_apply_scenarios


class ParseVersionTest(base.BaseTestCase):

    def test_all_ints(self):
        self.assertEqual([1, 0, 1], semver.parse_version('1.0.1'))

    def test_not_int(self):
        self.assertEqual([1, 'a', 1], semver.parse_version('1.a.1'))

    def test_short(self):
        self.assertEqual([1, 1, 0], semver.parse_version('1.1'))


class RulesTest(base.BaseTestCase):

    scenarios = [

        ('no existing versions, 1.0.0',
         {'new_version': [1, 0, 0],
          'existing_versions': [],
          'expected': ['first version in repository does not start with 0']}),
        ('no existing versions, 0.1.0',
         {'new_version': [0, 1, 0],
          'existing_versions': [],
          'expected': []}),

        ('existing series, next minor number',
         {'new_version': [1, 1, 0],
          'existing_versions': [[0, 1, 0], [1, 0, 0]],
          'expected': []}),
        ('existing series, next patch number',
         {'new_version': [1, 1, 2],
          'existing_versions': [[0, 1, 0], [1, 0, 0], [1, 1, 1]],
          'expected': []}),
        ('existing series, next patch number in existing minor release',
         {'new_version': [1, 1, 2],
          'existing_versions': [[0, 1, 0], [1, 0, 0], [1, 1, 1], [1, 2, 0]],
          'expected': []}),
        ('existing series, extra patch number',
         {'new_version': [1, 1, 3],
          'existing_versions': [[0, 1, 0], [1, 0, 0], [1, 1, 1]],
          'expected': [("new version '1.1.3' increments patch version "
                        "more than one over '1.1.1'")]}),
        ('existing series, extra patch number in existing minor release',
         {'new_version': [1, 1, 3],
          'existing_versions': [[0, 1, 0], [1, 0, 0], [1, 1, 1], [1, 2, 0]],
          'expected': [("new version '1.1.3' increments patch "
                        "version more than one over '1.1.1'")]}),
        ('existing series, extra minor number',
         {'new_version': [1, 3, 0],
          'existing_versions': [[0, 1, 0], [1, 0, 0], [1, 1, 1]],
          'expected': [("new version '1.3.0' increments minor version "
                        "more than one over '1.1.1'")]}),

        ('next major number',
         {'new_version': [2, 0, 0],
          'existing_versions': [[0, 1, 0], [1, 0, 0]],
          'expected': ["'2.0.0' is a major version increment over '1.0.0'"]}),

        # Taken from oslo.config
        ('next minor, with name tags',
         {'new_version': [1, 7, 0],
          'existing_versions': [
              [1, 4, 0, '0a5'],
              [1, 5, 0],
              [1, 6, 0],
              [2013, '1b1'],
              [2013, '1b2'],
              [2013, '1b3'],
              [2013, '1b4'],
              [2013, '1b5'],
              ['grizzly-eol'],
              ['havana-eol']],
          'expected': []}),

        ('already released',
         {'new_version': [1, 0, 0],
          'existing_versions': [[0, 1, 0], [1, 0, 0]],
          'expected': ["version '1.0.0' already exists in repository"]}),

        # From a bad tag in python-neutronclient
        ('improper alpha version tag',
         {'new_version': [3, 0, 0],
          'existing_versions': [[3, 0, 'a1']],
          'expected': []}),
    ]

    def test(self):
        msgs = semver.sanity_check_version(self.new_version,
                                           self.existing_versions)
        self.assertEqual(self.expected, msgs)
