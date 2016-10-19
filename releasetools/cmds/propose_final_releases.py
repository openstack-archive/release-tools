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
import atexit
import glob
import os.path
import re
import shutil
import tempfile

import yaml

from releasetools import gitutils
from releasetools import governance

PROJECT_TEMPLATE = '''\
      - repo: {repo}
        hash: {hash}'''

VERSION_TEMPLATE = '''\
  - version: {version}
    {diff_start_comment}diff-start: {diff_start}
    projects:
{projects}
'''

PRE_RELEASE = re.compile('(a|b|rc)')


def get_prior_branch_point(workdir, repo, branch):
    """Return the tag of the base of the branch.

    The diff-start is the old version is the tag on the commit where
    we created the branch. To determine that, we need to clone the
    repo and look at the branch.

    See
    http://lists.openstack.org/pipermail/openstack-dev/2016-October/104901.html
    for a better description of what the desired tag info is.

    """
    gitutils.clone_repo(workdir, repo)
    branch_base = gitutils.get_branch_base(
        workdir, repo, branch,
    )
    if branch_base:
        return gitutils.get_latest_tag(
            workdir, repo, branch_base,
        )
    # Work backwards from the most recent commit looking for the first
    # version that is not a pre-release, and assume that is the
    # previous release on a non-branching repository like for the
    # os-*-config tools.
    start = None
    while True:
        print('  looking for version before {}'.format(start))
        version = gitutils.get_latest_tag(workdir, repo, start)
        if not version:
            return None
        if not PRE_RELEASE.search(version):
            return version
        start = '{}^'.format(version)
    return version


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
        '--no-cleanup',
        dest='cleanup',
        default=True,
        action='store_false',
        help='do not remove temporary files',
    )
    parser.add_argument(
        '--all',
        default=False,
        action='store_true',
        help='process all deliverables, including release:cycle-trailing',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='produce detailed output',
    )
    parser.add_argument(
        'prior_series',
        help='the name of the previous series',
    )
    parser.add_argument(
        'series',
        help='the name of the release series to work on'
    )
    args = parser.parse_args()

    deliverables_dir = os.path.join(args.releases_repo, 'deliverables')
    if not os.path.exists(deliverables_dir):
        parser.error('{} does not exist'.format(deliverables_dir))

    team_data = governance.get_team_data(args.project_list)
    teams = [
        governance.Team(n, i)
        for n, i in team_data.items()
    ]
    deliverables = {
        d.name: d
        for t in teams
        for d in t.deliverables.values()
    }

    workdir = tempfile.mkdtemp(prefix='releases-')
    print('creating temporary files in %s' % workdir)

    def cleanup_workdir():
        if args.cleanup:
            try:
                shutil.rmtree(workdir)
            except Exception:
                pass
        else:
            print('not cleaning up %s' % workdir)
    atexit.register(cleanup_workdir)

    pattern = os.path.join(deliverables_dir,
                           args.series, '*.yaml')
    if args.verbose:
        print('Scanning {}'.format(pattern))
    deliverable_files = sorted(glob.glob(pattern))

    for filename in deliverable_files:
        if args.verbose:
            print('\n{}'.format(filename))
        deliverable_name = os.path.basename(filename)[:-5]
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
        for pre_rel in ['a', 'b', 'rc']:
            if pre_rel in str(latest_release['version']):
                break
        else:  # we did not find any pre_rel
            if args.verbose:
                    print('#  not a release candidate')
            continue
        deliverable = deliverables.get(deliverable_name)
        if deliverable and 'release:cycle-trailing' in deliverable.tags:
            if args.verbose:
                print('#  {} is a cycle-trailing project'.format(deliverable_name))
            if not args.all:
                continue
        # The new version is the same as the latest release version
        # without the pre-release component at the end. Make sure it
        # has 3 sets of digits.
        new_version = '.'.join(
            (latest_release['version'].split('.')[:-1] + ['0'])[:3]
        )
        branch = 'stable/{}'.format(args.prior_series)
        diff_start = get_prior_branch_point(
            workdir, projects[0]['repo'], branch,
        )
        deliverable_data['releases'].append({
            'version': new_version,
            'diff_start': diff_start,
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
            diff_start=diff_start,
            diff_start_comment=('# ' if diff_start is None else ''),
            projects=projects,
        ).rstrip() + '\n'
        with open(filename, 'a') as f:
            f.write(new_block)
