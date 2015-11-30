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

"""Lists the most recent versions in the deliverable files.
"""

from __future__ import print_function

import argparse

from releasetools import gitutils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'deliverable_file',
        nargs='*',
        help='paths to YAML files specifying releases',
    )
    parser.add_argument(
        '--releases-repo', '-r',
        default='.',
        help='path to the releases repository for automatic scanning',
    )
    args = parser.parse_args()

    results = gitutils.get_modified_deliverable_file_content(
        args.releases_repo,
        args.deliverable_file,
    )
    for deliverable_name, series_name, version, repo, hash in results:
        print('%s %s %s %s %s' %
              (deliverable_name, series_name, version, repo, hash))
    return 0


if __name__ == '__main__':
    main()
