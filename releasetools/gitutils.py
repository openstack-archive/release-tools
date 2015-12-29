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

import os.path
import subprocess

import yaml


def find_modified_deliverable_files(reporoot):
    "Return a list of files modified by the most recent commit."
    results = subprocess.check_output(
        ['git', 'diff', '--name-only', '--pretty=format:', 'HEAD^'],
        cwd=reporoot,
    )
    filenames = [
        l.strip()
        for l in results.splitlines()
        if l.startswith('deliverables/')
    ]
    return filenames


def get_modified_deliverable_file_content(reporoot, filenames):
    """Return a sequence of tuples containing the new versions.

    Return tuples containing (deliverable name, series name, version
    number, list of repositories).
    """
    # Determine which deliverable files to process by taking our
    # command line arguments or by scanning the git repository
    # for the most recent change.
    deliverable_files = filenames
    if not deliverable_files:
        deliverable_files = find_modified_deliverable_files(
            reporoot
        )

    for basename in deliverable_files:
        filename = os.path.join(reporoot, basename)
        with open(filename, 'r') as f:
            deliverable_data = yaml.load(f.read())

        # Determine where to send email announcements of
        # releases. Default to the development list, to cut down on
        # excessive emails to the announcement list.
        send_announcements_to = deliverable_data.get(
            'send-announcements-to',
            'openstack-dev@lists.openstack.org',
        )

        # The series name is part of the filename, rather than the file
        # body. That causes release.sh to be called with series="_independent"
        # for release:independent projects, and release.sh to use master branch
        # to evaluate fixed bugs.
        series_name = os.path.basename(
            os.path.dirname(os.path.abspath(filename))
        )
        deliverable_name = os.path.splitext(os.path.basename(filename))[0]

        all_versions = {
            rel['version']: rel for rel in deliverable_data['releases']
        }
        version = deliverable_data['releases'][-1]['version']
        this_version = all_versions[version]
        for project in this_version['projects']:
            yield (deliverable_name, series_name, version,
                   project['repo'], project['hash'],
                   send_announcements_to)
