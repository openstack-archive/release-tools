#!/usr/bin/python
#
# Handle pre-release / post-release ACLs for milestone-driven projects
#
# Copyright 2016 Thierry Carrez <thierry@openstack.org>
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

import argparse
import getpass
import os
import sys

import requests
import yaml

from releasetools import governance

GERRIT_URL = 'https://review.openstack.org/'

EXCEPTIONS = ['openstack/training-labs',
              'openstack/murano-apps',
              'openstack/trove-image-builder']


def repositories_list():
    """Yields (team, repo) tuples for cycle-with-milestones deliverables"""

    repos = governance.get_repositories(governance.get_team_data(),
                                        tags=['release:cycle-with-milestones'])
    for repo in repos:
        if repo.name not in EXCEPTIONS:
            yield(repo.deliverable.team.name, repo.name)


def patch_acls(args):
    """Handles the acls action"""

    blob = """[access "refs/heads/stable/{branch}"]
abandon = group Change Owner
abandon = group Project Bootstrappers
abandon = group {group}
exclusiveGroupPermissions = abandon label-Code-Review label-Workflow
label-Code-Review = -2..+2 group Project Bootstrappers
label-Code-Review = -2..+2 group {group}
label-Code-Review = -1..+1 group Registered Users
label-Workflow = -1..+0 group Change Owner
label-Workflow = -1..+1 group Project Bootstrappers
label-Workflow = -1..+1 group {group}

"""
    # Load repo/aclfile mapping from Gerrit config
    projectsyaml = os.path.join(args.repository, 'gerrit', 'projects.yaml')
    acl = {}
    config = yaml.load(open(projectsyaml))
    for project in config:
        aclfilename = project.get('acl-config')
        if aclfilename:
            acl[project['project']] = aclfilename[19:]
        else:
            acl[project['project']] = project['project'] + '.config'

    # Get the list of ACL files to update
    aclfiles = {}
    for team, repo in repositories_list():
        try:
            aclfiles[acl[repo]] = team
        except KeyError:
            print('No ACL file defined for %s' % repo)
            sys.exit(1)

    for aclfn, teamname in aclfiles.items():
        newcontent = ''
        fullfilename = os.path.join(args.repository, 'gerrit', 'acls', aclfn)
        group = '%s-release-branch' % teamname
        print('Patching %s' % fullfilename)
        if args.dryrun:
            print('Adding stable/%s ACL with rights for %s' %
                  (args.series, group))
        else:
            with open(fullfilename) as aclfile:
                hit = False
                for line in aclfile:
                    if line.startswith("[receive]"):
                        newcontent += blob.format(
                            branch=args.series,
                            group=group)
                        hit = True
                    newcontent += line
                if not hit:
                    print("Could not update %s automatically" % fullfilename)

            with open(fullfilename, 'w') as aclfile:
                aclfile.write(newcontent)


def gerrit_group_membership_test(action, group, member):
    """Test for Gerrit group membership based on action taken"""

    call = '/groups/%s/groups/%s' % (group, member)
    r = requests.get(GERRIT_URL + call)
    if action == 'PUT':
        # For PUT operations, return true if member is not already there
        return r.status_code != 200
    else:
        # For DELETE operations, return true if member already there
        return r.status_code == 200


def modify_gerrit_groups(args):
    """Handles the 'groups' action"""

    if args.stage == 'pre_release':
        # At pre-release stage we want to have $PROJECT-release and
        # Release Managers (and remove $PROJECT-stable-maint if present)
        actions = [
            ('PUT', lambda x: '%s-release' % x),
            ('PUT', lambda x: 'Release Managers'),
            ('DELETE', lambda x: '%s-stable-maint' % x),
        ]
    elif args.stage == 'post_release':
        # At post-release stage we want to have $PROJECT-stable-maint
        # (and remove Release Managers and $PROJECT-release if present)
        actions = [
            ('PUT', lambda x: '%s-stable-maint' % x),
            ('DELETE', lambda x: 'Release Managers'),
            ('DELETE', lambda x: '%s-release' % x),
        ]

    # Build the list of calls to make
    print('Computing the list of modifications')
    calls = set()
    for team, _ in repositories_list():
        group = '%s-release-branch' % team
        for (verb, memberformat) in actions:
            member = memberformat(team)
            # Filter based on already-handled names
            if gerrit_group_membership_test(verb, group, member):
                calls.add((verb, group, member))
            else:
                print("Skipping %s %s in %s (already done)" %
                      (verb, member, group))

    gerritauth = requests.auth.HTTPDigestAuth(args.username, getpass.getpass())
    for verb, group, member in calls:
        call = 'a/groups/%s/groups/%s' % (group, member)
        print('Updating %s group using %s %s' % (group, verb, call))
        if not args.dryrun:
            r = requests.request(verb, GERRIT_URL + call, auth=gerritauth)
            if r.status_code not in (201, 204):
                print('Error (%d) while updating group' % r.status_code)


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dryrun',
        default=False,
        help='do not actually do anything',
        action='store_true')
    subparsers = parser.add_subparsers(title='commands')
    do_acls = subparsers.add_parser(
        'acls',
        help='patch ACL files')
    do_acls.add_argument(
        'repository',
        help='location of the local project-config repository')
    do_acls.add_argument(
        'series',
        help='series to generate ACL for')
    do_acls.set_defaults(func=patch_acls)
    do_groups = subparsers.add_parser(
        'groups',
        help='modify Gerrit groups membership')
    do_groups.add_argument(
        'stage',
        choices=['pre_release', 'post_release'],
        help='type of modification to push')
    do_groups.add_argument(
        'username',
        help='gerrit HTTP username')
    do_groups.set_defaults(func=modify_gerrit_groups)
    args = parser.parse_args(args)
    if args.dryrun:
        print('Running in dry run mode, no action will be actually taken')
    return args.func(args)


if __name__ == '__main__':
    main()
