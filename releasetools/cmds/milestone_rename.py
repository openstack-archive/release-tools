#!/usr/bin/env python
#
# Script to rename Launchpad milestones
#
# Copyright 2014 Thierry Carrez <thierry@openstack.org>
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
import sys

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description='Rename Launchpad milestones')
    parser.add_argument('project', help='Project the milestone is defined in')
    parser.add_argument('from_milestone', help='Milestone to rename')
    parser.add_argument('to_milestone', help='New milestone name')
    parser.add_argument("--test", action='store_const', const='staging',
                        default='production', help='Use LP staging server to test')
    args = parser.parse_args()

    # Connect to Launchpad
    print("Connecting to Launchpad...")
    try:
        launchpad = Launchpad.login_with('openstack-releasing', args.test)
    except Exception as error:
        abort(2, 'Could not connect to Launchpad: ' + str(error))

    # Retrieve project
    try:
        project = launchpad.projects[args.project]
    except KeyError:
        abort(2, 'Could not find project: %s' % args.project)

    # Retrieve milestone
    milestone = project.getMilestone(name=args.from_milestone)
    if milestone is None:
        abort(2, 'Could not find milestone %s in project %s' % (
              args.from_milestone, args.project))

    milestone.name = args.to_milestone
    milestone.code_name = ''
    milestone.lp_save()
    print("Renamed")
