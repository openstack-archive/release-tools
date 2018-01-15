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
This tool will list bugs that were fixed in project master.
"""

import argparse
import re

from git import cmd
from git import Repo


BUG_PATTERN = r'Bug:\s+#?(?P<bugnum>\d+)'
STORYBOARD_PATTERN = r'Story:\s+#?(?P<storynum>\d+)'
CHANGEID_PATTERN = r'Change-Id:\s+(?P<id>[0-9a-zA-Z]+)'


def _parse_args():
    parser = argparse.ArgumentParser(
        description='List bugs with recent fixes.')
    parser.add_argument(
        '--repo', '-r',
        default='.',
        help='path to the openstack project repository',
    )
    parser.add_argument(
        '--start', '-s', required=True,
        help='git hash to start search from')
    parser.add_argument(
        '--stop', '-st',
        help='git hash to stop search to',
    )
    parser.add_argument(
        '--skip-backported', '-B',
        action='store_true',
        help='whether to skip patches backported to all stable branches',
    )
    parser.add_argument(
        '--easy-backport', '-e',
        action='store_true',
        default=False,
        help='whether to include easy (no git conflicts) backports only',
    )
    parser.add_argument(
        '--include-storyboard', '-sb',
        action='store_true',
        default=False,
        help='whether to also include storyboard entries (stories)',
    )
    return parser.parse_args()


def _backported_to_all_stable_branches(repo, id_):
    for ref in repo.refs:
        if ref.name.startswith('origin/stable/'):
            for commit in repo.iter_commits('..%s' % ref.name):
                if id_ == _extract_changeid(commit):
                    break
            else:
                return False
    return True


def _extract_changeid(commit):
    for match in re.finditer(CHANGEID_PATTERN, commit.message):
        id_ = match.group('id')
        return id_


def _is_easy_backport(repo, commit):
    g_cmd = cmd.Git(working_dir=repo.working_tree_dir)
    for ref in repo.refs:
        # consider a patch easy to backport if only it cleanly applies to all
        # stable branches; otherwise it will potentially require more work to
        # resolve git conflicts
        if ref.name.startswith('origin/stable/'):
            # before applying any patches, make sure the tree is clean and
            # fully reflects remote head
            g_cmd.clean(force=True, d=True, x=True)
            g_cmd.reset(hard=True)
            g_cmd.checkout(ref.name)
            try:
                g_cmd.cherry_pick(commit.hexsha)
            except cmd.GitCommandError:
                # cherry-pick does not have a 'dry run' mode, so we need to
                # actually clean up after a failure
                g_cmd.cherry_pick(abort=True)
                return False
    return True


def main():
    args = _parse_args()

    repo = Repo(args.repo)

    # make sure that we work with the latest code
    repo.remotes.origin.fetch()

    latest = repo.refs[args.stop if args.stop else 'origin/master'].commit
    rev = '%s..%s' % (args.start, latest.hexsha)

    # avoid duplicates
    bugs = set()

    for commit in repo.iter_commits(rev):
        id_ = _extract_changeid(commit)
        if id_ is None:
            # probably a merge commit, skip
            continue

        # skip patches backported into all branches
        if (args.skip_backported and
                _backported_to_all_stable_branches(repo, id_)):
            continue

        # skip patches that result in git conflicts in any of stable branches
        if (args.easy_backport and
                not _is_easy_backport(repo, commit)):
            continue

        # collect every bug number mentioned in the message
        for match in re.finditer(BUG_PATTERN, commit.message):
            bugs.add(match.group('bugnum'))
        if (args.include_storyboard):
            for match in re.finditer(STORYBOARD_PATTERN, commit.message):
                bugs.add('storyboard:' + match.group('storynum'))

    for bug in bugs:
        print(bug)


if __name__ == '__main__':
    main()
