# All Rights Reserved.
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

from __future__ import print_function

import argparse
import glob
import os.path

import yaml


def get_latest_deliverable_versions(deliverable_files, verbose):
    for filename in deliverable_files:
        if verbose:
            print('\n{}'.format(filename))
        with open(filename, 'r') as f:
            deliverable_data = yaml.safe_load(f)
        deliverable_name = os.path.basename(filename)[:-5]  # drop .yaml
        releases = deliverable_data.get('releases')
        if not releases:
            if verbose:
                print('#  no releases')
            continue
        latest_release = releases[-1]
        projects = latest_release.get('projects')
        if not projects:
            if verbose:
                print('#  no projects')
            continue
        yield(
            (deliverable_data['team'].lower(),
             deliverable_name,
             latest_release['version'],
             filename)
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--releases-repo', '-r',
        default='.',
        help='path to the releases repository for automatic scanning',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='produce detailed output',
    )
    parser.add_argument(
        'series',
        help='the name of the release series to work on'
    )
    args = parser.parse_args()

    deliverables_dir = os.path.join(args.releases_repo, 'deliverables')
    if not os.path.exists(deliverables_dir):
        parser.error('{} does not exist'.format(deliverables_dir))

    pattern = os.path.join(deliverables_dir,
                           args.series, '*.yaml')
    if args.verbose:
        print('Scanning {}'.format(pattern))
    deliverable_files = sorted(glob.glob(pattern))

    deliverables = sorted(get_latest_deliverable_versions(
        deliverable_files, args.verbose)
    )
    for team, deliverable, version, filename in deliverables:
        print('{:<25} {}'.format(deliverable, version))
