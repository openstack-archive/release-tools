#!/usr/bin/env python
#
# Script to apply bulk changes to Launchpad bugs
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
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
import argparse

import lazr.restfulclient.errors

from releasetools import launchpadutils

# Parameters
parser = argparse.ArgumentParser(description="Change Launchpad bugs in bulk")
parser.add_argument('projectname', help='The project to act on')
launchpadutils.add_cli_arguments(parser)
bugsfrom = parser.add_mutually_exclusive_group()
bugsfrom.add_argument('--status', default='Fix Committed',
                      help='All bugs with that status')
bugsfrom.add_argument('--milestone', help='All open bugs from this milestone')
parser.add_argument('--settarget',
                    help='ACTION: set the milestone to specified target')
parser.add_argument('--fixrelease', action='store_true',
                    help='ACTION: mark bugs fix released')
parser.add_argument('exceptions', type=int, nargs='*', help='Bugs to ignore')

args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = launchpadutils.login(args)

# Retrieve bugs
print("Retrieving project...")
proj = launchpad.projects[args.projectname]
changes = True
failed = set()

if args.settarget:
    to_milestone = proj.getMilestone(name=args.settarget)
    if not to_milestone:
        parser.error('Target milestone %s does not exist' % args.milestone)

if args.milestone:
    open_status = ['New', 'Incomplete', 'Confirmed', 'Triaged', 'In Progress']
    from_milestone = proj.getMilestone(name=args.milestone)
    if not from_milestone:
        parser.error('Origin milestone %s does not exist' % args.milestone)

while changes:
    changes = False
    if args.milestone:
        bugtasks = from_milestone.searchTasks(status=open_status)
    else:
        bugtasks = proj.searchTasks(status=args.status)

    # Process bugs
    for b in bugtasks:
        bug = b.bug
        # Skip bugs which triggered timeouts in previous runs
        if bug.id in failed:
            continue
        # If the action is settarget and you're not in milestone selection
        # mode, skip already-milestoned bugs with a different milestone
        if (not args.milestone) and (args.settarget and b.milestone):
            if b.milestone.name != args.settarget:
                continue
        print(bug.id, end='')
        if bug.id in args.exceptions:
            print(" - excepted")
            continue
        if args.settarget:
            if b.milestone != to_milestone:
                b.milestone = to_milestone
                print(" - milestoned", end='')
            else:
                print(" - milestone already set", end='')
        if args.fixrelease:
            print(" - fixreleased", end='')
            b.status = 'Fix Released'
        try:
            b.lp_save()
            if (args.settarget and not b.milestone) or args.fixrelease:
                changes = True
        except lazr.restfulclient.errors.ServerError as e:
            print(" - TIMEOUT during save !", end='')
            failed.add(bug.id)
        except Exception as e:
            print(" - ERROR during save ! (%s)" % e, end='')
            failed.add(bug.id)
        print()

if failed:
    print()
    print("Some bugs could not be automatically updated due to LP timeouts:")
    for bugid in failed:
        print("http://bugs.launchpad.net/bugs/%d" % bugid)
