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
"""Check a proposed new release version against other existing versions.
"""

from __future__ import print_function

import argparse
import sys

from releasetools import semver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'new_version',
        help='the new version being proposed',
    )
    parser.add_argument(
        'existing_versions',
        nargs='*',
        help='the existing versions in the repository',
    )
    args = parser.parse_args()

    new_version = semver.parse_version(args.new_version)
    if len(new_version) < 3:
        new_version = new_version + [0]
    existing_versions = sorted([
        semver.parse_version(v)
        for v in args.existing_versions
    ])
    msgs = semver.sanity_check_version(new_version, existing_versions)
    for msg in msgs:
        print(msg)
    return 1 if msgs else 0
