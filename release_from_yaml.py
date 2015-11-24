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

"""Tags a release as requested in a YAML file in the releases repo.
"""

from __future__ import print_function

import argparse
import os.path
import subprocess
import sys

import yaml

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

    tools_dir = os.path.dirname(sys.argv[0])

    # Determine which deliverable files to process by taking our
    # command line arguments or by scanning the git repository
    # for the most recent change.
    deliverable_files = args.deliverable_file
    if not deliverable_files:
        deliverable_files = gitutils.find_modified_deliverable_files(
            args.releases_repo,
        )

    errors = []
    for basename in deliverable_files:
        filename = os.path.join(args.releases_repo, basename)
        with open(filename, 'r') as f:
            deliverable_data = yaml.load(f.read())

        # The series name is part of the filename, rather than the file
        # body. That causes release.sh to be called with series="_independent"
        # for release:independent projects, and release.sh to use master branch
        # to evaluate fixed bugs.
        series_name = os.path.basename(
            os.path.dirname(os.path.abspath(filename))
        )

        all_versions = {
            rel['version']: rel for rel in deliverable_data['releases']
        }
        version = deliverable_data['releases'][-1]['version']
        print('Version %s' % version)
        this_version = all_versions[version]

        for project in this_version['projects']:
            cmd = [
                os.path.join(tools_dir, 'release.sh'),
                project['repo'],
                series_name,
                version,
                project['hash'],
            ]
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as err:
                print('ERROR: %s' % err)
                errors.append('Error with %s: %s' % (project['repo'], err))

    if errors:
        print('\nRepeating errors:')
        for e in errors:
            print(e)
        return 1
    return 0


if __name__ == '__main__':
    main()
