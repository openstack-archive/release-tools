#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
This Launchpad tool is used to tag bugs with a tag.
"""

import argparse
import sys

from launchpadlib.launchpad import Launchpad


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Tag tags with a tag.')
    parser.add_argument(
        'tag', help='Tag to use')
    return parser.parse_args()


def main():
    args = _parse_args()
    lp = Launchpad.login_with('openstack-releasing', 'production')
    bugnums = [line.strip() for line in sys.stdin.readlines()]
    for bugnum in bugnums:
        if bugnum:
            bug = lp.bugs[bugnum]
            tag = args.tag
            tags = bug.tags
            if tag not in tags:
                tags.append(tag)
                bug.tags = tags
                bug.lp_save()


if __name__ == '__main__':
    main()
