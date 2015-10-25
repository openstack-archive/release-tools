#!/usr/bin/env python
#
# Script to move bugs and blueprints to final release milestone page
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
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
import sys

import launchpadlib.launchpad
import lazr.restfulclient.errors

# Parameters
parser = argparse.ArgumentParser(description="Consolidate milestone pages"
                                 " at release time")
parser.add_argument('project', help='project to act on')
parser.add_argument('series', help='series to handle')
parser.add_argument('release', help='release milestone')
parser.add_argument('--copytask', action='store_true',
                    help='Enable CopyTask mode')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument('--dryrun', action='store_true',
                    help='Do not actually do anything')

args = parser.parse_args()

if args.dryrun:
    print("Dry run, nothing will actually change.")

statuses = ['New', 'Incomplete', 'Confirmed', 'Triaged', 'In Progress',
            'Fix Committed', 'Fix Released']

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = launchpadlib.launchpad.Launchpad.login_with('openstack-releasing',
                                                        args.test, version='devel')

# Retrieve FixCommitted bugs
print("Retrieving %s project..." % args.project)
proj = launchpad.projects[args.project]
if not proj:
    print("Project %s not found" % args.project)
    sys.exit(1)

print("Retrieving %s series..." % args.series)
series = proj.getSeries(name=args.series)
if not series:
    print("Series %s not found in project %s" % (args.series, args.project))
    sys.exit(1)

print("Checking %s release milestone..." % args.release)
release = proj.getMilestone(name=args.release)
if not release:
    print("%s is not a %s milestone!" % (args.release, args.project))
    sys.exit(1)

print("Retrieving milestones for %s..." % args.series)
seriesmilestones = series.all_milestones
milestones = []
release_is_in_series = False
for milestone in seriesmilestones:
    if milestone == release:
        release_is_in_series = True
    else:
        if (args.project == "swift" and
            not milestone.name.startswith(
                release.name + "-rc")):
            continue
        milestones.insert(0, milestone)
print("Found")
for milestone in milestones:
    print(milestone.name)
print()

if not release_is_in_series:
    print("%s is not a %s milestone!" % (args.release, args.series))
    sys.exit(1)

# Process blueprints
print("Moving all %s blueprints to %s..." % (series.name, release.name))
for bp in series.valid_specifications:
    if bp.milestone in milestones:
        print(bp.name)
        if not args.dryrun:
            bp.milestone = release
            bp.lp_save()
            print(" - released",)
        if not bp.is_complete:
            print(" (not completed!)",)
        print()

# Process bugs
for milestone in milestones:
    if args.copytask:
        print("CopyTasking %s bugs to %s..." % (milestone.name, release.name))
    else:
        print("Moving %s bugs to %s..." % (milestone.name, release.name))
    bugsleft = True
    while bugsleft:
        failed = set()
        bugsleft = False
        for bt in proj.searchTasks(status=statuses, milestone=milestone):
            bug = bt.bug
            print(bug.id)
            if not args.dryrun:
                if args.copytask:
                    try:
                        newbt = bug.addTask(target=series)
                        newbt.assignee = bt.assignee
                        newbt.status = bt.status
                        newbt.importance = bt.importance
                        newbt.milestone = release
                        newbt.lp_save()
                        print(" - copytasked")
                        bugsleft = True
                    except lazr.restfulclient.errors.BadRequest:
                        print(" - task already exists, skipping")
                else:
                    bt.milestone = release
                    try:
                        bt.lp_save()
                        print(" - released")
                    except lazr.restfulclient.errors.ServerError as e:
                        print(" - TIMEOUT during save !",)
                        failed.add(bug.id)
                    bugsleft = True
            if bt.status != 'Fix Released':
                print(" (not in FixReleased status!)",)
            print()
        if failed:
            print()
            print("Some bugs could not be automatically updated "
                  "due to LP timeouts:")
            for bugid in failed:
                print("http://bugs.launchpad.net/bugs/%d" % bugid)
    print()
