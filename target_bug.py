#!/usr/bin/env python
#
# Script to set the milestone of Launchpad bugs
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

from __future__ import print_function

from argparse import ArgumentParser
from launchpadlib.launchpad import Launchpad
from lazr.restfulclient.errors import ServerError

# Parameters
parser = ArgumentParser(description="Change Launchpad bug targets")
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument('projectname', help='The project to act on')
parser.add_argument('milestone',
                    help='ACTION: set the milestone to specified target')
parser.add_argument('bugs', type=int, nargs='+', help='Bugs to update')

args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = Launchpad.login_with('openstack-releasing', args.test)

# Retrieve bugs
print("Retrieving project...")
proj = launchpad.projects[args.projectname]

to_milestone = proj.getMilestone(name=args.milestone)
if not to_milestone:
    parser.error('Target milestone %s does not exist' % args.milestone)

for bug_id in args.bugs:
    bug = launchpad.bugs[bug_id]
    for task in bug.bug_tasks:
        if task.bug_target_name != args.projectname:
            continue
        print('%s - ' % bug.id, end='')
        if task.milestone == args.milestone:
            print('already set')
        else:
            try:
                task.milestone = args.milestone
                task.lp_save()
            except ServerError as e:
                print('FAILED to update: %s' % e)
            else:
                print('milestone updated')
