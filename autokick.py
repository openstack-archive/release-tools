#!/usr/bin/python
#
# Script to automatically adjust series goal based on target milestone
# in Launchpad blueprints, and possibly remove unprioritized blueprints
#
# Copyright 2013 Thierry Carrez <thierry@openstack.org>
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

from argparse import ArgumentParser
from launchpadlib.launchpad import Launchpad
import sys


# Parse arguments
parser = ArgumentParser(description="Adjust blueprint series goal/milestones")
parser.add_argument('projectname', help='Project or projectgroup to act on')
parser.add_argument('seriesname', help='Series to act on')
parser.add_argument('--nokick', action='store_true',
                    help='Do not kick unprioritized BPs out of milestones')
parser.add_argument('--dryrun', action='store_true',
                    help='Just show what would be done')
args = parser.parse_args()

kickmessage = "You should not set a milestone target unless the blueprint" \
              " has been properly prioritized by the project drivers."

# Log into LP
lp = Launchpad.login_with('adjust-series-goal', 'production', version='devel')

try:
    projectgroup = lp.project_groups[args.projectname]
    projects = projectgroup.projects
except (KeyError, AttributeError):
    try:
        projects = [lp.projects[args.projectname], ]
    except KeyError:
        print "%s: no such project or projectgroup" % args.projectname
        sys.exit(1)

for project in projects:
    print "== %s ==" % project.name
    series = project.getSeries(name=args.seriesname)

    # Get the milestones for the series
    milestones = []
    try:
        active_milestones = series.active_milestones_collection
    except AttributeError:
        print "No milestone in series %s for %s, skipping" % \
            (args.seriesname, project.name)
        continue
    for ms in series.active_milestones_collection:
        milestones.append(ms)

    # Get the blueprints with seriesgoal set
    accepted = series.valid_specifications

    # Find targeted blueprints that are not in the series
    for bp in project.valid_specifications:
        if bp.milestone in milestones:
            if bp.priority in ["Undefined", "Not"]:
                # Blueprint is in milestone but has no priority
                if not args.nokick:
                    print "KICK %s (from %s)" % (bp.name, bp.milestone.name)
                    if not args.dryrun:
                        bp.proposeGoal(goal=None)
                        bp.milestone = None
                        if bp.whiteboard is None:
                            bp.whiteboard = ""
                        if kickmessage not in bp.whiteboard:
                            bp.whiteboard += ("\n\n" + kickmessage + "\n")
                            bp.whiteboard += "(This is an automated message)\n"
                        bp.lp_save()
            else:
                if bp not in accepted:
                    # BP has milestone & prio, but not accepted for series yet
                    print "SETGOAL %s" % bp.name
                    if not args.dryrun:
                        bp.proposeGoal(goal=series)

    # Get the blueprints in the series
    proposed = []
    for bp in series.all_specifications:
        if not bp.is_complete:
            if bp.milestone not in milestones:
                # Blueprint is in series, no milestone
                print "CLEARGOAL %s" % bp.name
                if not args.dryrun:
                    bp.proposeGoal(goal=None)
            else:
                if not bp.has_accepted_goal:
                    if bp.priority not in ["Undefined", "Not"]:
                        # BP is proposed/declined in series, has mstone + prio
                        print "APPROVEGOAL %s" % bp.name
                        if not args.dryrun:
                            bp.acceptGoal()
