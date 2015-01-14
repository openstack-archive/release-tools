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
"""Check a proposed new release version against other existing versions.
"""

from __future__ import print_function

import argparse
import sys


def try_int(val):
    try:
        return int(val)
    except ValueError:
        return val


def parse_version(v):
    parts = v.split('.')
    if len(parts) < 3:
        parts.append('0')
    return [try_int(p) for p in parts]


def format_version(v):
    return '.'.join(str(p) for p in v)


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

    new_version = parse_version(args.new_version)
    if len(new_version) < 3:
        new_version = new_version + [0]
    existing_versions = sorted([
        parse_version(v)
        for v in args.existing_versions
    ])
    msgs = apply_rules(new_version, existing_versions)
    for msg in msgs:
        print(msg)
    return 1 if msgs else 0


def apply_rules(new_version, existing_versions):
    if not existing_versions:
        if new_version[0] != 0:
            return ['first version in repository does not start with 0']
        return []
    if new_version in existing_versions:
        return ['version %r already exists in repository' %
                format_version(new_version)]
    same_minor = same_major = None
    for v in existing_versions:
        # Look for other numbers in the series
        if v[:2] == new_version[:2]:
            print('%r in same minor series as %r' %
                  (format_version(v), format_version(new_version)))
            if not same_minor or v > same_minor:
                same_minor = v
        if v[:1] == new_version[:1]:
            print('%r in same major series as %r' %
                  (format_version(v), format_version(new_version)))
            if not same_major or v > same_major:
                same_major = v
    if same_minor is not None:
        print('last version in minor series %r' %
              format_version(same_minor))
        actual = same_minor[2] + 1
        expected = new_version[2]
        if expected != actual:
            return ['new version %r increments patch version more than one over %r' % 
                    (format_version(new_version), format_version(same_minor))]
    if same_major is not None and same_major != same_minor:
        print('last version in major series %r' %
              format_version(same_major))
        if new_version > same_major:
            actual = same_major[1] + 1
            expected = new_version[1]
            if actual > expected:
                return ['new version %r increments minor version more than one over %r' % 
                        (format_version(new_version), format_version(same_major))]
            if new_version[2] != 0:
                return ['new version %r increments minor version and patch version' %
                        format_version(new_version)]
    latest_version = existing_versions[-1]
    if new_version[0] > latest_version[0]:
        return ['%r is a major version increment over %r' %
                (format_version(new_version), format_version(latest_version))]
    return []


if __name__ == '__main__':
    sys.exit(main())
