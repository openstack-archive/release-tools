#!/usr/bin/env python
#
# Script to prepare bugs with no activity for expiration
#
# Copyright (c) 2015 Thales Services SAS
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
from argparse import ArgumentParser
import datetime

from launchpadlib.launchpad import Launchpad
from lazr.restfulclient.errors import ServerError
import pytz


# Parameters
parser = ArgumentParser(
    description="Unset assignee/milestone for bugs with no activity in bulk")
parser.add_argument('projectname', help='The project to act on')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument("--dry-run", action='store_true',
                    help="Don't actually perform any action")
parser.add_argument("--days", type=int, default=365,
                    help='days without activity (default: %(default)s days)')
parser.add_argument('exceptions', type=int, nargs='*', help='Bugs to ignore')

args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = Launchpad.login_with('openstack-prepare-expire', args.test)

# Retrieve bugs
print("Retrieving project...")
proj = launchpad.projects[args.projectname]
failed = set()

modified_before = (
    datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=args.days))

# Get bugtasks, older first
open_statuses = ['New', 'Incomplete', 'Confirmed', 'Triaged', 'In Progress']
bugtasks = proj.searchTasks(
    order_by='date_last_updated', status=open_statuses)

# Process bugs
content = (
    "This bug is > %s days without activity. We are unsetting assignee "
    "and milestone and setting status to Incomplete in order to allow "
    "its expiry in 60 days.\n\n"
    "If the bug is still valid, then update the bug status.") % args.days

for bugtask in bugtasks:
    bug = bugtask.bug

    # Process bugs with no activity after modified_before
    if bug.date_last_updated > modified_before:
        break

    # Skip bugs which triggered timeouts in previous runs
    if bug.id in failed:
        continue

    print(bug.id, end='')
    if bug.id in args.exceptions:
        print(" - excepted")
        continue

    if bugtask.assignee:
        bugtask.assignee = None
        print(" - unset assignee", end='')
    if bugtask.milestone:
        bugtask.milestone = None
        print(" - unset milestone", end='')
    if bugtask.status != 'Incomplete':
        bugtask.status = 'Incomplete'
        print(" - set status Incomplete", end='')

    if not args.dry_run:
        try:
            bugtask.lp_save()
            bug.lp_save()
            bug.newMessage(content=content)
            print(" - DONE!", end='')
        except ServerError:
            print(" - TIMEOUT!", end='')
            failed.add(bug.id)
        except Exception as e:
            print(" - ERROR! (%s)" % e, end='')
            failed.add(bug.id)
    print()

if failed:
    print()
    print("Some bugs could not be automatically updated due to LP timeouts:")
    for bugid in failed:
        print("http://bugs.launchpad.net/bugs/%d" % bugid)
