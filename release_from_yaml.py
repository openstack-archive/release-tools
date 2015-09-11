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

"""Publish a release as requested in a YAML file in the releases repo.
"""

from __future__ import print_function

import argparse
import os.path
import sys
import subprocess
import tempfile

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'deliverable_file',
        help='a path to a YAML file specifying releases',
    )
    parser.add_argument(
        'version',
        nargs='?',
        help='version to be released, defaults to ensuring all of them',
    )
    args = parser.parse_args()

    tools_dir = os.path.dirname(sys.argv[0])

    with open(args.deliverable_file, 'r') as f:
        deliverable_data = yaml.load(f.read())

    print(deliverable_data)

    # The series name is part of the filename, rather than the file
    # body.
    series_name = os.path.basename(
        os.path.dirname(os.path.abspath(args.deliverable_file))
    )

    all_versions = {
        rel['version']: rel for rel in deliverable_data['releases']
    }
    version = args.version
    if not version:
        version = deliverable_data['releases'][-1]['version']
        print('Defaulting version to last listed')

    print('Version %s' % version)
    this_version = all_versions[version]

    if this_version.get('highlights'):
        highlights_file = tempfile.NamedTemporaryFile()
        highlights_file.write(this_version['highlights'])
        highlights_file.flush()
    else:
        highlights_file = None

    # NOTE(dhellmann): For now we only support one project, until
    # we rewrite the release script.
    this_hash = [p['hash'] for p in this_version['projects']][0]
    cmd = [
        os.path.join(tools_dir, 'release_postversion.sh'),
        series_name,
        version,
        this_hash,
        deliverable_data['launchpad'],
    ]
    if highlights_file:
        cmd.append('')  # empty email tags argument required
        cmd.append(highlights_file.name)
    print(' '.join(cmd))
    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
