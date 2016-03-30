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

from releasetools import governance

PROJECT_TEMPLATE = '''\
      - repo: {repo}
        hash: {hash}'''

VERSION_TEMPLATE = '''\
  - version: {version}
    projects:
{projects}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=governance.PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
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

    for filename in deliverable_files:
        if args.verbose:
            print('\n{}'.format(filename))
        with open(filename, 'r') as f:
            deliverable_data = yaml.safe_load(f)
        releases = deliverable_data.get('releases')
        if not releases:
            if args.verbose:
                print('#  no releases')
            continue
        latest_release = releases[-1]
        projects = latest_release.get('projects')
        if not projects:
            if args.verbose:
                print('#  no projects')
            continue
        if 'rc' not in latest_release['version']:
            if args.verbose:
                print('#  not a release candidate')
            continue
        new_version = latest_release['version'].split('.0rc')[0]
        deliverable_data['releases'].append({
            'version': new_version,
            'projects': latest_release['projects'],
        })
        print('new version for {}: {}'.format(os.path.basename(filename),
                                              new_version))

        # NOTE(dhellmann): PyYAML doesn't preserve layout when you
        # write the data back out, so do the formatting ourselves.
        projects = '\n'.join(PROJECT_TEMPLATE.format(**p)
                             for p in latest_release['projects'])
        new_block = VERSION_TEMPLATE.format(
            version=new_version,
            projects=projects,
        ).rstrip() + '\n'
        with open(filename, 'a') as f:
            f.write(new_block)
