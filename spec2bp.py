#!/usr/bin/python
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
import os
import re
import requests
from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(
    description="Set blueprint fields for an approved spec file")
parser.add_argument('specfile', help='spec file (in a -specs git repo)')
parser.add_argument('milestone', help='which milestone to target the BP to')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument("--priority", default='Low',
                    choices=['Essential', 'High', 'Medium', 'Low'],
                    help='which priority to set (default is Low)')

args = parser.parse_args()

# Validate specfile
m = re.match(r".*/(\w+)-specs/(.+)/(.+).rst", os.path.abspath(args.specfile))
if m is None:
    parser.error("%s has not a recognized spec pattern" % args.specfile)
projname = m.group(1)
repoloc = "openstack/%s-specs/plain/%s" % (projname, m.group(2))
bpname = m.group(3)

# Check that spec was approved (merged in specs repository)
# Also use this to validate spec link URL
cgit = "http://git.openstack.org/cgit"
specurl = "%s/%s/%s.rst" % (cgit, repoloc, bpname)
try:
    r = requests.get(specurl)
    if r.status_code != 200 or not r.text:
        parser.error("No such confirmed spec in %s-specs" % projname)
except requests.exceptions.RequestException as exc:
    parser.exit(1, "Error trying to confirm spec is valid")

# Log into Launchpad
launchpad = Launchpad.login_with('openstack-releasing', args.test,
                                 version='devel')

# Validate project
project = launchpad.projects[projname]
if not project:
    parser.error("%s project does not exist in Launchpad" % projname)

# Validate milestone
milestone = project.getMilestone(name=args.milestone)
if not milestone:
    parser.error("%s milestone does not exist in Launchpad" % args.milestone)
if not milestone.is_active:
    parser.error("%s is no longer an active milestone" % args.milestone)

# Validate spec
bp = project.getSpecification(name=bpname)
if not bp:
    parser.exit(1, "Blueprint %s not found for project %s"
                % (bpname, projname))

# Set approver, definition status, spec URL, priority and milestone
bp.approver = launchpad.me
bp.definition_status = 'Approved'
bp.specification_url = specurl
bp.priority = args.priority
bp.milestone = milestone
bp.lp_save()
