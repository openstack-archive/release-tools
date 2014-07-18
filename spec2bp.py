#!/usr/bin/env python
#
# Script to set fields in LP blueprint for an approved spec
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
import re
import requests
from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(
    description="Set blueprint fields for an approved spec file")
parser.add_argument('project', help='project name')
parser.add_argument('blueprint', help='blueprint name')
parser.add_argument('--in-review', action='store_true',
                    help='spec is still under review, mark as Blocked')
parser.add_argument('--milestone', help='which milestone to target the BP to')
parser.add_argument("--priority",
                    choices=['Essential', 'High', 'Medium', 'Low'],
                    help='priority to set (default is keep, or set Low)')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')

args = parser.parse_args()

# Log into Launchpad
launchpad = Launchpad.login_with('openstack-releasing', args.test,
                                 version='devel')

# Validate project
project = launchpad.projects[args.project]
if not project:
    parser.error("%s project does not exist in Launchpad" % args.project)

# Validate spec
bp = project.getSpecification(name=args.blueprint)
if not bp:
    parser.error("Blueprint %s not found for project %s"
                 % (args.blueprint, args.project))

# If no milestone is set on blueprint, we must have a milestone argument
if not bp.milestone and not args.milestone:
    parser.error("Blueprint has no milestone, so you must specify one to set "
                 "using the --milestone argument")

# Validate milestone if provided
if args.milestone:
    milestone = project.getMilestone(name=args.milestone)
    if not milestone:
        parser.error("%s milestone does not exist in LP" % args.milestone)
    if not milestone.is_active:
        parser.error("%s is no longer an active milestone" % args.milestone)
else:
    milestone = bp.milestone

# Calculate likely spec location
path = None

if bp.specification_url:
    m = re.match(r"(.*git.openstack.org.*/\w+-specs)/(.+)/(.+).rst",
                 bp.specification_url)
    if m is not None:
        # This looks like a valid spec link, so we'll use that
        # but make sure we look at plain specs docs
        if m.group(2).startswith("plain/"):
            path = m.group(2)[6:]
        else:
            path = m.group(2)
        site = m.group(1)
        spec = m.group(3)

if not path:
    site = "http://git.openstack.org/cgit/openstack/%s-specs" % args.project
    path = "specs/%s" % milestone.series_target.name
    spec = args.blueprint

url = "%s/plain/%s/%s.rst" % (site, path, spec)

# Set blueprints fields
if args.in_review:
    # Check if the spec is not already approved
    try:
        r = requests.get(url)
        if r.status_code == 200 and r.text:
            parser.error("The spec you want to set --in-review seems to "
                         "have been approved already!")
    except requests.exceptions.RequestException as exc:
        pass
    bp.definition_status = 'Review'
    bp.implementation_status = 'Blocked'

else:
    # Check that spec was approved (merged in specs repository)
    # Also use this to validate spec link URL
    try:
        r = requests.get(url)
        if r.status_code != 200 or not r.text:
            parser.error("""
Can't find the spec corresponding to the blueprint in cgit. There are
multiple possible causes for that.

The spec may not be approved yet. If you just wanted to set fields on
unapproved BP, don't forget the --in-review parameter.

The spec may also point to some non-standard URL (not specs/series/bpname.rst).
In that case, you can workaround the issue by setting the spec URL in the
blueprint itself.""")
    except requests.exceptions.RequestException as exc:
        parser.exit(1, "Error trying to confirm spec is valid")

    # Set approver, definition status, spec URL, priority and milestone
    bp.definition_status = 'Approved'
    bp.specification_url = url
    if bp.implementation_status == 'Blocked':
        bp.implementation_status = 'Unknown'

bp.approver = launchpad.me
if bp.priority == 'Undefined':
    bp.priority = args.priority or 'Low'
if bp.milestone != milestone:
    bp.milestone = milestone
    bp.lp_save()
    bp.proposeGoal(goal=milestone.series_target)
else:
    bp.lp_save()
